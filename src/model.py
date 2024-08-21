from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete='CASCADE'))
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime)


class LatestLocation(Base):
    __tablename__ = "latest_locations"
    device_id = Column(Integer, ForeignKey("devices.id", ondelete='CASCADE'), primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete='CASCADE'))

