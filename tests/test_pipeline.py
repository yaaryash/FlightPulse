
from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Flight
from app.pipeline import save_flights, normalize_flights

from app.pipeline import (
    generate_fingerprint,
    normalize_callsign,
    normalize_flight,
    normalize_flights,
    parse_timestamp,
)


def sample_flight():
    return {
        "icao24": " ABC123 ",
        "callsign": " AI101 ",
        "origin_country": " India ",
        "time_position": 1799999900,
        "last_contact": 1799999990,
        "longitude": 73.0,
        "latitude": 19.0,
        "baro_altitude": 10000.0,
        "velocity": 220.0,
        "on_ground": False,
    }


def test_normalize_callsign():
    assert normalize_callsign(" AI101 ") == "AI101"
    assert normalize_callsign("   ") is None
    assert normalize_callsign(None) is None


def test_parse_timestamp():
    result = parse_timestamp(1799999990)
    assert isinstance(result, datetime)
    assert result.tzinfo is None
    assert parse_timestamp(None) is None
    assert parse_timestamp("invalid") is None


def test_normalize_flight_fields():
    flight = normalize_flight(sample_flight())

    assert flight is not None
    assert flight["icao24"] == "abc123"
    assert flight["callsign"] == "AI101"
    assert flight["origin_country"] == "India"
    assert flight["latitude"] == 19.0


def test_reject_flight_without_identifier():
    raw = sample_flight()
    raw["icao24"] = " "

    assert normalize_flight(raw) is None


def test_fingerprint_is_stable():
    flight = normalize_flight(sample_flight())
    assert flight is not None

    assert generate_fingerprint(flight) == generate_fingerprint(flight)


def test_remove_duplicate_records_from_batch():
    raw = sample_flight()
    records = normalize_flights([raw, raw.copy()])

    assert len(records) == 1
    assert len(records[0]["fingerprint"]) == 64


def make_test_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_save_flights_and_prevent_repeat_duplicates():
    db = make_test_session()
    try:
        raw = {
            "icao24": "abc123",
            "callsign": "AI101",
            "origin_country": "India",
            "last_contact": 1799999990,
            "longitude": 73.0,
            "latitude": 19.0,
            "velocity": 220.0,
            "on_ground": False,
        }
        records = normalize_flights([raw])

        first = save_flights(records, db)
        second = save_flights(records, db)

        assert first["inserted"] == 1
        assert second["inserted"] == 0
        assert second["duplicates"] == 1

        saved = db.scalars(select(Flight)).all()
        assert len(saved) == 1
    finally:
        db.close()


def test_pipeline_normalizes_fixture_records():
    fixture = {
        "icao24": "abc123",
        "callsign": " AI101 ",
        "origin_country": "India",
        "last_contact": 1799999990,
        "longitude": 73.0,
        "latitude": 19.0,
        "velocity": 220.0,
        "on_ground": False,
    }

    result = normalize_flights([fixture])

    assert len(result) == 1
    assert result[0]["icao24"] == "abc123"
    assert result[0]["callsign"] == "AI101"
    assert len(result[0]["fingerprint"]) == 64
