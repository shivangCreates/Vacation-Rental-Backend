import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schemas.availability import (
    UnavailablePeriodCreate,
    UnavailablePeriodResponse,
)
from ..schemas.property import PropertyCreate, PropertyResponse
from ..services.property_service import (
    create_property,
    create_unavailable_period,
    delete_unavailable_period,
    get_property_by_id,
    get_unavailable_periods,
    search_properties,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/properties", tags=["Properties"])


def validate_search_dates(check_in: date | None, check_out: date | None) -> None:
    if (check_in is None) != (check_out is None):
        raise HTTPException(
            status_code=422,
            detail="Provide both check-in and check-out dates.",
        )
    if check_in is not None and check_out is not None and check_out <= check_in:
        raise HTTPException(
            status_code=422,
            detail="Check-out must be after check-in.",
        )


@router.get("/", response_model=list[PropertyResponse])
def get_properties(
    db: Session = Depends(get_db),
    destination: str | None = None,
    guests: int | None = None,
    budget_per_night: float | None = None,
    property_type: str | None = None,
    check_in: date | None = None,
    check_out: date | None = None,
    amenities: list[str] | None = Query(default=None),
):
    validate_search_dates(check_in, check_out)
    return search_properties(
        db=db,
        destination=destination,
        guests=guests,
        budget_per_night=budget_per_night,
        property_type=property_type,
        amenities=amenities,
        check_in=check_in,
        check_out=check_out,
    )


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
):
    property_data = get_property_by_id(db, property_id)

    if property_data is None:
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )

    return property_data


@router.post("/", response_model=PropertyResponse, status_code=201)
def add_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_property(
            db=db,
            property_data=property_data.model_dump()
        )
    except Exception as error:
        db.rollback()
        logger.exception("Failed to create property")
        raise HTTPException(
            status_code=500,
            detail="Failed to create property"
        ) from error


@router.get(
    "/{property_id}/unavailability",
    response_model=list[UnavailablePeriodResponse],
)
def list_unavailability(
    property_id: int,
    db: Session = Depends(get_db),
):
    if get_property_by_id(db, property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return get_unavailable_periods(db, property_id)


@router.post(
    "/{property_id}/unavailability",
    response_model=UnavailablePeriodResponse,
    status_code=201,
)
def add_unavailability(
    property_id: int,
    period: UnavailablePeriodCreate,
    db: Session = Depends(get_db),
):
    if get_property_by_id(db, property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")

    try:
        return create_unavailable_period(
            db=db,
            property_id=property_id,
            check_in=period.check_in,
            check_out=period.check_out,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except Exception as error:
        db.rollback()
        logger.exception("Failed to add unavailable period for property %s", property_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to update property availability",
        ) from error


@router.delete(
    "/{property_id}/unavailability/{period_id}",
    status_code=204,
)
def remove_unavailability(
    property_id: int,
    period_id: int,
    db: Session = Depends(get_db),
):
    if get_property_by_id(db, property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")
    if not delete_unavailable_period(db, property_id, period_id):
        raise HTTPException(status_code=404, detail="Unavailable period not found")
    return Response(status_code=204)