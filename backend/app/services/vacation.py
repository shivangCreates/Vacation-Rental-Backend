
from datetime import date
from pydantic import BaseModel, Field


class VacationRequirements(BaseModel):
    destination: str | None = None
    check_in: date | None = None
    check_out: date | None = None

    guests: int | None = Field(default=None, ge=1, le=50)

    budget_per_night: float | None = Field(
        default=None,
        gt=0,
    )

    property_type: str | None = None

    amenities: list[str] = Field(default_factory=list)
