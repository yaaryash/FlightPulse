from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, func, select
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
    query = (
        select(
            Flight.origin_country.label("country"),
            func.count(Flight.id).label("flight_count"),
        )
        .group_by(Flight.origin_country)
        .order_by(func.count(Flight.id).desc())
        .limit(limit)
    )

    if country:
        query = query.where(
            Flight.origin_country.ilike(f"%{country.strip()}%")
        )

    results = db.execute(query).all()

    return [
        {"country": row.country, "flight_count": row.flight_count}
        for row in results
    ]

@router.get("/summary")
def flight_summary(
    db: Annotated[Session, Depends(get_db)],
    country: str | None = None,
):
    query = select(
        func.count(Flight.id).label("total_flights"),
        func.avg(Flight.velocity).label("average_velocity"),
        func.sum(
            func.cast(Flight.on_ground, Integer)
        ).label("on_ground_count"),
    )

    if country:
        query = query.where(
            Flight.origin_country.ilike(f"%{country.strip()}%")
        )

    result = db.execute(query).one()

    return {
        "country_filter": country,
        "total_flights": result.total_flights or 0,
        "average_velocity": (
            round(result.average_velocity, 2)
            if result.average_velocity is not None
            else None
        ),
        "on_ground_count": result.on_ground_count or 0,
    }
