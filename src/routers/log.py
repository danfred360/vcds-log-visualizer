from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import Group, Log, get_db
from ..vcds_parser import VCDSParser

log_router = APIRouter()


@log_router.post("/upload/")
async def upload_csv(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file format")

    parser = VCDSParser()
    parsed_data = parser.parse_csv(file)

    # Extract metadata
    created_at = parsed_data["created_at"]
    vin = parsed_data["vin"]
    motor_type = parsed_data["motor_type"]
    groups = parsed_data["groups"]

    log = Log(
        name="Example Log",
        description=f"Log for VIN {vin} with motor type {motor_type}",
        created_at=created_at,
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
        "log_id": log.id,
        "created_at": created_at,
        "vin": vin,
        "motor_type": motor_type,
    }


@log_router.get("/{log_id}")
def get_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


# route at route that takes top query parameter to determine how many logs to return and pagination
@log_router.get("/")
def get_logs(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    logs = db.query(Log).offset(offset).limit(limit).all()
    return logs


@log_router.delete("/")
def delete_all_logs(db: Session = Depends(get_db)):
    db.query(Group).delete()
    db.query(Log).delete()
    db.commit()
    return {"message": "All logs deleted successfully"}


@log_router.get("/{log_id}/groups/")
def get_groups_by_log_id(log_id: int, db: Session = Depends(get_db)):
    groups = db.query(Group).filter(Group.log_id == log_id).all()
    if not groups:
        raise HTTPException(status_code=404, detail="Groups not found")
    return groups


@log_router.get("/groups/")
def get_groups(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    groups = db.query(Group).offset(offset).limit(limit).all()
    return groups
