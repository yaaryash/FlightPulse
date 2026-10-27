
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Flight
from app.schemas import FlightResponse

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get("/", response_model=list[FlightResponse])
def list_flights(
    db: Annotated[Session, Depends(get_db)],
    country: str | None = None,
    on_ground: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    query = select(Flight)

    if country:
        query = query.where(
            Flight.origin_country.ilike(f"%{country.strip()}%")
        )

    if on_ground is not None:
        query = query.where(Flight.on_ground == on_ground)

    query = query.order_by(Flight.last_contact.desc())
    query = query.offset(offset).limit(limit)

    try:
        return db.scalars(query).all()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve flight records",
        ) from exc
