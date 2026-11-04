from datetime import date

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.property import Property, PropertyAmenity, PropertyUnavailablePeriod


def search_properties(
    db: Session,
    destination: str | None = None,
    guests: int | None = None,
    budget_per_night: float | None = None,
    property_type: str | None = None,
    amenities: list[str] | None = None,
    check_in: date | None = None,
    check_out: date | None = None,
) -> list[Property]:
    if (check_in is None) != (check_out is None):
        raise ValueError("Both check-in and check-out dates are required.")
    if check_in is not None and check_out is not None and check_out <= check_in:
        raise ValueError("Check-out must be after check-in.")

    query = db.query(Property)

    if destination:
        query = query.filter(
            Property.destination.ilike(f"%{destination}%")
        )

    if guests is not None:
        query = query.filter(
            Property.max_guests >= guests
        )

    if budget_per_night is not None:
        query = query.filter(
            Property.price_per_night <= budget_per_night
        )

    if property_type:
        query = query.filter(
            Property.property_type.ilike(f"%{property_type}%")
        )

    if check_in is not None and check_out is not None:
        query = query.filter(
            ~Property.unavailable_periods.any(
                (PropertyUnavailablePeriod.check_in < check_out)
                & (PropertyUnavailablePeriod.check_out > check_in)
            )
        )

    for amenity in amenities or []:
        normalized_amenity = amenity.strip().lower()
        if not normalized_amenity:
            continue

        amenity_filter = (
            func.lower(func.trim(PropertyAmenity.name)) == normalized_amenity
        )
        if normalized_amenity in {"pool", "swimming pool"}:
            query = query.filter(
                or_(
                    Property.has_pool.is_(True),
                    Property.amenity_entries.any(
                        func.lower(func.trim(PropertyAmenity.name)).in_(
                            ("pool", "swimming pool")
                        )
                    ),
                )
            )
        else:
            query = query.filter(Property.amenity_entries.any(amenity_filter))

    return query.all()


def get_property_by_id(db: Session, property_id: int):
    return db.query(Property).filter(
        Property.id == property_id
    ).first()


def create_property(db: Session, property_data: dict) -> Property:
    property_values = dict(property_data)
    amenities = property_values.pop("amenities", [])
    new_property = Property(**property_values)
    new_property.amenities = amenities
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    return new_property


def get_unavailable_periods(
    db: Session,
    property_id: int,
) -> list[PropertyUnavailablePeriod]:
    return (
        db.query(PropertyUnavailablePeriod)
        .filter(PropertyUnavailablePeriod.property_id == property_id)
        .order_by(PropertyUnavailablePeriod.check_in)
        .all()
    )


def create_unavailable_period(
    db: Session,
    property_id: int,
    check_in: date,
    check_out: date,
) -> PropertyUnavailablePeriod:
    overlaps = (
        db.query(PropertyUnavailablePeriod)
        .filter(
            PropertyUnavailablePeriod.property_id == property_id,
            PropertyUnavailablePeriod.check_in < check_out,
            PropertyUnavailablePeriod.check_out > check_in,
        )
        .first()
    )
    if overlaps is not None:
        raise ValueError("This period overlaps an existing unavailable period.")

    period = PropertyUnavailablePeriod(
        property_id=property_id,
        check_in=check_in,
        check_out=check_out,
    )
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def delete_unavailable_period(
    db: Session,
    property_id: int,
    period_id: int,
) -> bool:
    period = (
        db.query(PropertyUnavailablePeriod)
        .filter(
            PropertyUnavailablePeriod.id == period_id,
            PropertyUnavailablePeriod.property_id == property_id,
        )
        .first()
    )
    if period is None:
        return False

    db.delete(period)
    db.commit()
    return True