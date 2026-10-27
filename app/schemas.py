
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class FlightBase(BaseModel):
    icao24: str = Field(min_length=1, max_length=20)
    callsign: str | None = Field(default=None, max_length=20)
    origin_country: str = Field(min_length=1, max_length=100)
    time_position: datetime | None = None
    last_contact: datetime
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    baro_altitude: float | None = None
    velocity: float | None = Field(default=None, ge=0)
    on_ground: bool = False


class FlightCreate(FlightBase):
    fingerprint: str = Field(min_length=1, max_length=64)


class FlightResponse(FlightBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fingerprint: str
