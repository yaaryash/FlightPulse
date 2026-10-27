
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    icao24: Mapped[str] = mapped_column(String(20), index=True)
    callsign: Mapped[str | None] = mapped_column(String(20), nullable=True)
    origin_country: Mapped[str] = mapped_column(String(100), index=True)
    time_position: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_contact: Mapped[datetime] = mapped_column(DateTime, index=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    baro_altitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    velocity: Mapped[float | None] = mapped_column(Float, nullable=True)
    on_ground: Mapped[bool] = mapped_column(default=False)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    __table_args__ = (
        Index("ix_flights_country_contact", "origin_country", "last_contact"),
    )
