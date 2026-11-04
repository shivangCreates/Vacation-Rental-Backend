from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator


class UnavailablePeriodCreate(BaseModel):
    check_in: date
    check_out: date

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.check_out <= self.check_in:
            raise ValueError("Check-out must be after check-in.")
        return self


class UnavailablePeriodResponse(UnavailablePeriodCreate):
    id: int
    property_id: int

    model_config = ConfigDict(from_attributes=True)
