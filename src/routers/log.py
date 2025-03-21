import csv
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import Group, Log, get_db

log_router = APIRouter()


def parse_csv(file) -> Dict:
    reader = csv.reader(file)
    rows = list(reader)

    # Extract metadata from the top rows
    log_date = rows[0][0]  # Assuming the date is in the first cell of the first row
    vin = rows[0][5].split(":")[1].strip()  # Extract VIN from the first row
    motor_type = rows[2][
        0
    ].strip()  # Assuming motor type is in the first cell of the third row

    # Extract group names and sensor headers
    group_headers = rows[3]  # Group names (e.g., Group A, Group B, etc.)
    sensor_headers = rows[4]  # Sensor names (e.g., Engine speed, MAF, etc.)

    # Map group names to their sensor headers
    groups = {}
    for i, header in enumerate(group_headers):
        if header.startswith("Group"):
            group_name = header.strip(":")
            groups[group_name] = {
                "sensors": sensor_headers[
                    i : i + 5
                ]  # Adjust range based on CSV structure
            }

    # Parse sensor values
    for row in rows[5:]:  # Data rows
        timestamp = float(row[1])  # Assuming timestamp is in the second column
        for group_name, group_data in groups.items():
            for i, sensor in enumerate(group_data["sensors"]):
                if sensor:  # Skip empty sensor headers
                    value = row[i + 2]  # Adjust index based on CSV structure
                    group_data.setdefault("values", {}).setdefault(sensor, []).append(
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
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file format")

    # Parse CSV directly from the uploaded file
    parsed_data = parse_csv(file.file)

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


@log_router.get("/logs/{log_id}")
def get_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log
