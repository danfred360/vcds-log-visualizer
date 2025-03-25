import csv
import io
from datetime import datetime
from typing import Dict

from fastapi import UploadFile


class VCDSParser:
    def __init__(self):
        pass

    def parse_csv(self, file: UploadFile) -> Dict:
        # Read the entire file content
        file_content = file.file.read()

        try:
            text_file = io.StringIO(file_content.decode("utf-8"))
            reader = csv.reader(text_file)
            rows = list(reader)
        except UnicodeDecodeError:
            text_file = io.StringIO(file_content.decode("latin-1"))
            reader = csv.reader(text_file)
            rows = list(reader)

        # Extract metadata
        log_date = " ".join(rows[0][:4])  # Extract log date correctly
        created_at = datetime.strptime(log_date, "%A %d %B %Y")
        vin = rows[0][5].split("-VCID")[0].strip()  # Extract VIN (before -VCID)
        motor_type = rows[1][2].strip()  # Extract motor type correctly

        # Extract group names, sensor headers, and units
        group_headers = rows[3]  # Group names
        sensor_headers = rows[4]  # Sensor names
        units_headers = rows[5]  # Sensor units

        # Initialize groups dictionary
        groups = {}
        group_indices = {}

        for i, header in enumerate(group_headers):
            if header.startswith("Group"):
                group_name = header.strip(":")
                groups[group_name] = {
                    "sensors": [],
                    "values": {},
                }
                group_indices[group_name] = i  # Store group index

        # Map sensor names and units to groups
        for group_name, start_index in group_indices.items():
            for j in range(start_index + 1, len(sensor_headers)):
                if sensor_headers[j]:  # Ignore empty sensor names
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

        # Parse the data rows
        for row in rows[7:]:
            if not row or not row[1]:  # Ignore empty or malformed rows
                continue

            try:
                timestamp = float(row[1])  # Convert timestamp to float
            except ValueError:
                continue  # Skip rows with invalid timestamps

            for group_name, start_index in group_indices.items():
                group_data = groups[group_name]
                for i, sensor in enumerate(group_data["sensors"]):
                    sensor_index = start_index + 1 + i
                    if sensor_index < len(row):
                        value = row[sensor_index]
                        group_data["values"].setdefault(sensor["name"], []).append(
                            {
                                "timestamp": timestamp,
                                "value": float(value) if value else None,
                            }
                        )

        return {
            "created_at": created_at,
            "vin": vin,
            "motor_type": motor_type,
            "groups": groups,
        }
