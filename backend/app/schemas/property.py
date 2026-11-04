
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PropertyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    destination: str = Field(min_length=1, max_length=100)
    property_type: str = Field(min_length=1, max_length=50)
    price_per_night: float = Field(gt=0)
    max_guests: int = Field(gt=0)
    has_pool: bool = False
    description: str = Field(min_length=1, max_length=500)
    amenities: list[str] = Field(default_factory=list)

    @field_validator("amenities")
    @classmethod
    def normalize_amenities(cls, amenities: list[str]) -> list[str]:
        normalized = [amenity.strip() for amenity in amenities]
        if any(not amenity for amenity in normalized):
            raise ValueError("Amenities cannot be empty.")
        return list(dict.fromkeys(normalized))


class PropertyResponse(PropertyCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
