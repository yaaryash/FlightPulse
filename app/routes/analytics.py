
import pandas as pd
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Flight

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/countries")
def country_analytics(
    db: Annotated[Session, Depends(get_db)],
    country: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    query = select(
        Flight.origin_country,
        Flight.velocity,
        Flight.baro_altitude,
        Flight.on_ground,
    )

    if country and country.strip():
        query = query.where(
            Flight.origin_country.ilike(f"%{country.strip()}%")
        )

    rows = db.execute(query).mappings().all()
    df = pd.DataFrame([dict(row) for row in rows])

    if df.empty:
        return []

    # Pandas: group records by country and count flights.
    result = (
        df.groupby("origin_country")
        .size()
        .reset_index(name="flight_count")
        .sort_values(
            "flight_count",
            ascending=False,
            kind="stable",
        )
        .head(limit)
    )

    return [
        {
            "country": row["origin_country"],
            "flight_count": int(row["flight_count"]),
        }
        for _, row in result.iterrows()
    ]


@router.get("/summary")
def flight_summary(
    db: Annotated[Session, Depends(get_db)],
    country: str | None = None,
):
    query = select(
        Flight.origin_country,
        Flight.velocity,
        Flight.baro_altitude,
        Flight.on_ground,
    )

    if country and country.strip():
        query = query.where(
            Flight.origin_country.ilike(f"%{country.strip()}%")
        )

    rows = db.execute(query).mappings().all()
    df = pd.DataFrame([dict(row) for row in rows])

    if df.empty:
        return {
            "country_filter": country,
            "total_flights": 0,
            "average_velocity": None,
            "on_ground_count": 0,
        }

    # Pandas skips missing numeric values when calculating the mean.
    average_velocity = pd.to_numeric(
        df["velocity"], errors="coerce"
    ).mean()

    on_ground_count = (
        df["on_ground"].fillna(False).astype(bool).sum()
    )

    return {
        "country_filter": country,
        "total_flights": int(len(df)),
        "average_velocity": (
            round(float(average_velocity), 2)
            if pd.notna(average_velocity)
            else None
        ),
        "on_ground_count": int(on_ground_count),
    }
