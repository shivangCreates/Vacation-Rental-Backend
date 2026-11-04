
from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    destination: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    property_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    price_per_night: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    max_guests: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    has_pool: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    amenity_entries: Mapped[list["PropertyAmenity"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
    )
    amenities = association_proxy(
        "amenity_entries",
        "name",
        creator=lambda name: PropertyAmenity(name=name),
    )
    unavailable_periods: Mapped[list["PropertyUnavailablePeriod"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
    )


class PropertyAmenity(Base):
    __tablename__ = "property_amenities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    property: Mapped["Property"] = relationship(back_populates="amenity_entries")


class PropertyUnavailablePeriod(Base):
    __tablename__ = "property_unavailable_periods"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="ck_unavailable_dates_order"),
        Index(
            "ix_unavailable_property_dates",
            "property_id",
            "check_in",
            "check_out",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)

    property: Mapped["Property"] = relationship(back_populates="unavailable_periods")
