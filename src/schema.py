from datetime import datetime
from typing import List, Optional

import strawberry
from sqlalchemy.orm import Session

from src.model import Device
from src.sql_query import get_location_history_by_device, get_last_location_for_all_devices


@strawberry.type(name="Device")
class DeviceType:
    id: int
    name: str


@strawberry.type(name="Location")
class LocationType:
    id: int
    device_id: int
    latitude: float
    longitude: float
    timestamp: datetime


@strawberry.input
class DeviceCreateInput:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def all_devices(self, info) -> List[DeviceType]:
        session: Session = info.context['db']
        devices = session.query(Device).all()
        return [DeviceType(id=device.id, name=device.name) for device in devices]

    @strawberry.field
    def device_by_id(self, info, device_id: int) -> Optional[DeviceType]:
        session: Session = info.context['db']
        device = session.query(Device).filter(Device.id == device_id).first()
        if device:
            return DeviceType(id=device.id, name=device.name)
        return None

    @strawberry.field
    def location_history_by_device(self, info, device_id: int) -> List[LocationType]:
        session: Session = info.context['db']
        locations = get_location_history_by_device(device_id, session)
        return [
            LocationType(
                id=loc.id,
                device_id=loc.device_id,
                latitude=loc.latitude,
                longitude=loc.longitude,
                timestamp=loc.timestamp
            ) for loc in locations
        ]

    @strawberry.field
    def last_locations(self, info) -> List[LocationType]:
        session: Session = info.context['db']
        last_locations = get_last_location_for_all_devices(session)
        return last_locations


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_device(self, info, input: DeviceCreateInput) -> DeviceType:
        session: Session = info.context['db']
        db_device = Device(name=input.name)
        session.add(db_device)
        session.commit()
        return DeviceType(id=db_device.id, name=db_device.name)
