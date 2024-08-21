from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.model import Location, Device, LatestLocation


def get_location_history_by_device(device_id: int, db: Session):
    locations = db.query(Location).filter(Location.device_id == device_id).all()
    return locations


def get_last_location_for_all_devices(db: Session):
    last_locations = db.query(Location).join(LatestLocation, Location.id == LatestLocation.location_id).all()
    return last_locations
