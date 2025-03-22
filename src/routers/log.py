import csv
import io
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import Group, Log, get_db

log_router = APIRouter()


def parse_csv(file: UploadFile) -> Dict:
    # Read the entire file content into memory
    file_content = file.file.read()

    try:
        # Attempt to decode the file with utf-8 encoding
        text_file = io.StringIO(file_content.decode("utf-8"))
        reader = csv.reader(text_file)
        rows = list(reader)
    except UnicodeDecodeError:
        # Fallback to a more permissive encoding (e.g., latin-1)
        text_file = io.StringIO(file_content.decode("latin-1"))
        reader = csv.reader(text_file)
        rows = list(reader)

    # Extract metadata from the top rows
    log_date = ",".join(rows[0][:4])
    vin = rows[0][5].split(":")[1].strip()
    motor_type = rows[1][0].strip()

    # Extract group names and sensor headers
    group_headers = rows[3]  # Group names (e.g., Group A, Group B, etc.)
    sensor_headers = rows[4]  # Sensor names (e.g., Engine speed, MAF, etc.)
    units_headers = rows[5]  # Units or ranges for the sensors

    # Map group names to their sensor headers and units
    groups = {}
    for i, header in enumerate(group_headers):
        if header.startswith("Group"):
            group_name = header.strip(":")
            groups[group_name] = {
                "sensors": [],
            }
            # Dynamically map sensors and units for this group
            for j in range(i + 1, len(sensor_headers)):
                if sensor_headers[j]:  # Skip empty sensor headers
                    groups[group_name]["sensors"].append(
                        {
                            "name": sensor_headers[j].strip(),
                            "unit": (
                                units_headers[j].strip()
                                if j < len(units_headers)
                                else None
                            ),
                        }
                    )

    for row in rows[6:]:
        if not row or not row[0]:
            continue
        try:
            timestamp = float(row[1])
        except ValueError:
            continue

        for group_name, group_data in groups.items():
            for i, sensor in enumerate(group_data["sensors"]):
                sensor_index = i + 2  # Adjust index based on CSV structure
                if sensor_index < len(row):
                    value = row[sensor_index]
                    group_data.setdefault("values", {}).setdefault(
                        sensor["name"], []
                    ).append(
                        {
                            "timestamp": timestamp,
                            "value": float(value) if value else None,
                        }
                    )

    return {
        "log_date": log_date,
        "vin": vin,
        "motor_type": motor_type,
        "groups": groups,
    }


@log_router.post("/upload/")
async def upload_csv(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file format")

    # Parse CSV directly from the uploaded file
    parsed_data = parse_csv(file)

    # Extract metadata
    log_date = parsed_data["log_date"]
    vin = parsed_data["vin"]
    motor_type = parsed_data["motor_type"]
    groups = parsed_data["groups"]

    # Store in database
    log = Log(
        name="Example Log",
        description=f"Log for VIN {vin} with motor type {motor_type}",
        created_at=datetime.strptime(log_date, "%A,%d,%B,%Y"),  # Parse the date
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    for group_name, group_data in groups.items():
        group = Group(
            log_id=log.id, group_name=group_name, sensors=group_data["values"]
        )
        db.add(group)

    db.commit()
    return {
        "message": "CSV uploaded and parsed successfully",
        "log_date": log_date,
        "vin": vin,
        "motor_type": motor_type,
    }


@log_router.get("/{log_id}")
def get_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log
