from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.model import Location


def get_location_history_by_device(device_id: int, db: Session):
    locations = db.query(Location).filter(Location.device_id == device_id).all()
    return locations


def get_last_location_for_all_devices(db: Session):
    subquery = db.query(
        Location.device_id,
        func.max(Location.timestamp).label('last_timestamp')
    ).group_by(Location.device_id).subquery()

    last_locations = db.query(
        Location
    ).join(
        subquery,
        (Location.device_id == subquery.c.device_id) & (Location.timestamp == subquery.c.last_timestamp)
    ).all()

    return last_locations
