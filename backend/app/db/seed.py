
from app.db.database import SessionLocal
from app.models.property import Property


sample_properties = [
    {
        "name": "Cozy Mountain Cabin",
        "destination": "Manali",
        "property_type": "Cabin",
        "price_per_night": 3500,
        "max_guests": 4,
        "has_pool": False,
        "description": "A cozy mountain cabin with beautiful valley views.",
    },
    {
        "name": "Luxury Beach Villa",
        "destination": "Goa",
        "property_type": "Villa",
        "price_per_night": 8000,
        "max_guests": 6,
        "has_pool": True,
        "description": "A spacious villa with a private pool near the beach.",
    },
    {
        "name": "Budget City Apartment",
        "destination": "Jaipur",
        "property_type": "Apartment",
        "price_per_night": 2000,
        "max_guests": 3,
        "has_pool": False,
        "description": "An affordable apartment near popular city attractions.",
    },
    {
        "name": "Family Pool Villa",
        "destination": "Goa",
        "property_type": "Villa",
        "price_per_night": 6000,
        "max_guests": 8,
        "has_pool": True,
        "description": "A family-friendly villa with a swimming pool and garden.",
    },
]


def seed_properties():
    with SessionLocal() as db:
        for property_data in sample_properties:
            existing = (
                db.query(Property)
                .filter_by(name=property_data["name"])
                .first()
            )

            if existing is None:
                db.add(Property(**property_data))

        db.commit()
        print("Sample properties added successfully!")


if __name__ == "__main__":
    seed_properties()
