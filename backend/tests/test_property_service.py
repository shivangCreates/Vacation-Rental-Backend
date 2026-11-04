import os
import unittest
from datetime import date
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite://"

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.chat import chat
from app.api.properties import get_property, validate_search_dates
from app.db.database import Base, get_db
from app.main import app
from app.schemas.availability import UnavailablePeriodCreate
from app.schemas.chat import ChatRequest
from app.schemas.property import PropertyResponse
from app.schemas.vacation import VacationRequirements
from app.services.session_store import session_store
from app.services.property_service import (
    create_property,
    create_unavailable_period,
    delete_unavailable_period,
    search_properties,
)


class PropertyServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        app.dependency_overrides[get_db] = self.override_get_db
        self.client = TestClient(app)
        self.property = create_property(
            self.db,
            {
                "name": "Goa Villa",
                "destination": "Goa",
                "property_type": "Villa",
                "price_per_night": 5000,
                "max_guests": 4,
                "has_pool": True,
                "description": "Villa near the beach",
                "amenities": ["wifi", "air conditioning"],
            },
        )

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def override_get_db(self):
        with Session(self.engine) as db:
            yield db

    def test_pool_and_all_explicit_amenities_are_required(self):
        self.assertEqual(
            search_properties(self.db, amenities=["swimming pool", "wifi"]),
            [self.property],
        )
        self.assertEqual(
            search_properties(self.db, amenities=["wifi", "parking"]),
            [],
        )
        self.assertEqual(
            search_properties(self.db, amenities=["private pool"]),
            [],
        )
        self.assertEqual(
            PropertyResponse.model_validate(self.property).amenities,
            ["wifi", "air conditioning"],
        )

    def test_unavailable_dates_are_excluded_but_adjacent_dates_are_allowed(self):
        create_unavailable_period(
            self.db,
            self.property.id,
            date(2026, 11, 10),
            date(2026, 11, 15),
        )

        self.assertEqual(
            search_properties(
                self.db,
                check_in=date(2026, 11, 12),
                check_out=date(2026, 11, 14),
            ),
            [],
        )
        self.assertEqual(
            search_properties(
                self.db,
                check_in=date(2026, 11, 15),
                check_out=date(2026, 11, 17),
            ),
            [self.property],
        )

    def test_overlapping_unavailable_period_is_rejected(self):
        create_unavailable_period(
            self.db,
            self.property.id,
            date(2026, 11, 10),
            date(2026, 11, 15),
        )

        with self.assertRaisesRegex(ValueError, "overlaps"):
            create_unavailable_period(
                self.db,
                self.property.id,
                date(2026, 11, 14),
                date(2026, 11, 18),
            )

    def test_unavailable_period_can_be_removed(self):
        period = create_unavailable_period(
            self.db,
            self.property.id,
            date(2026, 11, 10),
            date(2026, 11, 15),
        )

        self.assertTrue(
            delete_unavailable_period(self.db, self.property.id, period.id)
        )
        self.assertEqual(
            search_properties(
                self.db,
                check_in=date(2026, 11, 12),
                check_out=date(2026, 11, 14),
            ),
            [self.property],
        )

    def test_property_lookup_for_missing_id_returns_404(self):
        with self.assertRaises(HTTPException) as error:
            get_property(999, self.db)

        self.assertEqual(error.exception.status_code, 404)

    def test_missing_property_endpoint_returns_404(self):
        response = self.client.get("/properties/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Property not found")

    def test_property_create_endpoint_returns_amenities(self):
        response = self.client.post(
            "/properties/",
            json={
                "name": "Jaipur Apartment",
                "destination": "Jaipur",
                "property_type": "Apartment",
                "price_per_night": 2500,
                "max_guests": 2,
                "description": "Central apartment",
                "amenities": ["wifi"],
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["amenities"], ["wifi"])

    def test_unavailability_endpoints_manage_calendar(self):
        response = self.client.post(
            f"/properties/{self.property.id}/unavailability",
            json={"check_in": "2026-11-10", "check_out": "2026-11-15"},
        )

        self.assertEqual(response.status_code, 201)
        period_id = response.json()["id"]
        listed = self.client.get(
            f"/properties/{self.property.id}/unavailability"
        )
        self.assertEqual(len(listed.json()), 1)

        removed = self.client.delete(
            f"/properties/{self.property.id}/unavailability/{period_id}"
        )
        self.assertEqual(removed.status_code, 204)

    def test_property_search_endpoint_applies_amenity_and_date_filters(self):
        create_unavailable_period(
            self.db,
            self.property.id,
            date(2026, 11, 10),
            date(2026, 11, 15),
        )

        unavailable = self.client.get(
            "/properties/",
            params={
                "check_in": "2026-11-12",
                "check_out": "2026-11-14",
                "amenities": ["wifi", "swimming pool"],
            },
        )
        self.assertEqual(unavailable.status_code, 200)
        self.assertEqual(unavailable.json(), [])

        incomplete = self.client.get(
            "/properties/",
            params={"check_in": "2026-11-12"},
        )
        self.assertEqual(incomplete.status_code, 422)

    def test_chat_with_one_date_asks_for_missing_date_without_failing(self):
        session_id = session_store.create_session()
        requirements = VacationRequirements(
            destination="Goa",
            check_in=date(2026, 11, 12),
        )

        try:
            with (
                patch(
                    "app.api.chat.extract_requirements",
                    return_value=requirements,
                ),
                patch(
                    "app.api.chat.generate_reply",
                    return_value="Please provide your check-out date.",
                ) as generate_reply,
            ):
                response = chat(
                    ChatRequest(session_id=session_id, message="Goa on November 12"),
                    self.db,
                )

            self.assertEqual(response.reply, "Please provide your check-out date.")
            self.assertIn("check-out", generate_reply.call_args.kwargs["availability_note"])
        finally:
            session_store.delete_session(session_id)

    def test_date_range_must_include_both_ordered_dates(self):
        with self.assertRaises(HTTPException) as missing_date:
            validate_search_dates(date(2026, 11, 10), None)
        self.assertEqual(missing_date.exception.status_code, 422)

        with self.assertRaises(HTTPException) as reversed_dates:
            validate_search_dates(date(2026, 11, 15), date(2026, 11, 10))
        self.assertEqual(reversed_dates.exception.status_code, 422)

    def test_unavailable_period_schema_rejects_reversed_dates(self):
        with self.assertRaises(ValueError):
            UnavailablePeriodCreate(
                check_in=date(2026, 11, 15),
                check_out=date(2026, 11, 10),
            )


if __name__ == "__main__":
    unittest.main()
