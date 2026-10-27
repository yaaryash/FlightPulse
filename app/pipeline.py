
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collector import fetch_flights
from app.database import SessionLocal
from app.models import Flight

logger = logging.getLogger(__name__)


def normalize_callsign(value: Any) -> str | None:
    """Trim whitespace and normalize empty callsigns to None."""
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    return cleaned or None


def parse_timestamp(value: Any) -> datetime | None:
    """Convert a Unix timestamp into a UTC-naive datetime for SQLite."""
    if value is None:
        return None

    try:
        timestamp = float(value)

        if not pd.notna(timestamp) or timestamp <= 0:
            return None

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        ).replace(tzinfo=None)

    except (TypeError, ValueError, OverflowError, OSError):
        logger.warning("Invalid timestamp: %r", value)
        return None


def normalize_flight(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Validate and normalize one flight record."""
    icao24 = raw.get("icao24")
    country = raw.get("origin_country")
    last_contact = parse_timestamp(raw.get("last_contact"))

    if not isinstance(icao24, str) or not icao24.strip():
        logger.warning("Skipping flight without a valid icao24")
        return None

    if not isinstance(country, str) or not country.strip():
        logger.warning("Skipping flight without an origin country")
        return None

    if last_contact is None:
        logger.warning("Skipping flight without a valid last_contact")
        return None

    icao24 = icao24.strip().lower()
    country = country.strip()
    callsign = normalize_callsign(raw.get("callsign"))

    def optional_float(value: Any) -> float | None:
        if value is None:
            return None

        try:
            number = float(value)

            if not pd.notna(number) or abs(number) == float("inf"):
                return None

            return number

        except (TypeError, ValueError, OverflowError):
            return None

    longitude = optional_float(raw.get("longitude"))
    latitude = optional_float(raw.get("latitude"))

    if longitude is not None and not -180 <= longitude <= 180:
        longitude = None

    if latitude is not None and not -90 <= latitude <= 90:
        latitude = None

    velocity = optional_float(raw.get("velocity"))

    if velocity is not None and velocity < 0:
        velocity = None

    altitude = optional_float(raw.get("baro_altitude"))
    time_position = parse_timestamp(raw.get("time_position"))

    return {
        "icao24": icao24,
        "callsign": callsign,
        "origin_country": country,
        "time_position": time_position,
        "last_contact": last_contact,
        "longitude": longitude,
        "latitude": latitude,
        "baro_altitude": altitude,
        "velocity": velocity,
        "on_ground": bool(raw.get("on_ground", False)),
    }


def generate_fingerprint(flight: dict[str, Any]) -> str:
    """Generate a deterministic fingerprint for a normalized flight state."""
    payload = {
        "icao24": flight["icao24"],
        "last_contact": flight["last_contact"].isoformat(),
        "longitude": flight["longitude"],
        "latitude": flight["latitude"],
        "velocity": flight["velocity"],
        "on_ground": flight["on_ground"],
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_flights(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize records, convert missing values, and deduplicate with Pandas."""
    normalized_records = []

    for raw in records:
        flight = normalize_flight(raw)

        if flight is None:
            continue

        flight["fingerprint"] = generate_fingerprint(flight)
        normalized_records.append(flight)

    if not normalized_records:
        return []

    df = pd.DataFrame(normalized_records)

    original_count = len(df)
    df = df.drop_duplicates(
        subset=["fingerprint"],
        keep="first",
    )

    duplicate_count = original_count - len(df)

    if duplicate_count:
        logger.info(
            "Pandas removed %s duplicate flight records",
            duplicate_count,
        )

    # Convert Pandas NaN/NaT values to Python None.
    df = df.astype(object).where(pd.notna(df), None)

    return df.to_dict(orient="records")


def save_flights(
    records: list[dict[str, Any]],
    db: Session,
) -> dict[str, int]:
    """Save normalized flight records without inserting duplicates."""
    inserted = 0
    duplicates = 0
    errors = 0

    for record in records:
        try:
            fingerprint = record["fingerprint"]

            existing = db.scalar(
                select(Flight.id).where(
                    Flight.fingerprint == fingerprint
                )
            )

            if existing is not None:
                duplicates += 1
                continue

            # Isolate each insert with a savepoint.
            with db.begin_nested():
                db.add(Flight(**record))
                db.flush()

            inserted += 1

        except Exception:
            errors += 1
            logger.exception(
                "Failed to save flight record",
                extra={"icao24": record.get("icao24")},
            )

    try:
        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Failed to commit flight records")
        raise

    logger.info(
        "Flight persistence completed: inserted=%s duplicates=%s errors=%s",
        inserted,
        duplicates,
        errors,
    )

    return {
        "inserted": inserted,
        "duplicates": duplicates,
        "errors": errors,
    }


async def run_pipeline() -> dict[str, int]:
    """Fetch, normalize, deduplicate, and persist flight records."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(20.0),
        follow_redirects=True,
    ) as client:
        raw_records = await fetch_flights(client)

    normalized_records = normalize_flights(raw_records)

    with SessionLocal() as db:
        result = save_flights(normalized_records, db)

    result["fetched"] = len(raw_records)
    result["normalized"] = len(normalized_records)

    return result
