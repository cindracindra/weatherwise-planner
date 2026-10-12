"""Tests for database/db_place.py: checking places, and scoping to the owner."""

from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from database.db_event import create_event
from database.db_place import (
    clean_place, create_place, delete_place, get_place_by_id, update_place,
)
from models.db_models.place import Place

OWNER, OTHER = 7, 8


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        yield app


@pytest.fixture
def session():
    """The SQLAlchemy session db_place opens, as a mock."""
    with patch("database.db_place.Session") as session_class:
        yield session_class.return_value.__enter__.return_value


def make_place(user_id=OWNER, **overrides):
    place = Place(
        name="Hyde Park", category="park", address=None, latitude=None,
        longitude=None, notes=None, suits_sunny=True, suits_cloudy=True,
        suits_rainy=False, temp_min=None, temp_max=None, visit_minutes=120,
        user_id=user_id)
    place.id = overrides.pop("id", 3)
    for key, value in overrides.items():
        setattr(place, key, value)
    return place


def payload(result):
    response, status = result
    return status, response.get_json()


FORM = {"name": "Kew Gardens", "category": "garden", "weather_form": "1",
        "suits_sunny": "on", "temp_min": "", "temp_max": "",
        "visit_minutes": "180", "latitude": "", "longitude": ""}


# ---------- clean_place ----------

def test_a_form_post_with_unticked_boxes():
    fields = clean_place(FORM)
    assert (fields["suits_sunny"], fields["suits_cloudy"],
            fields["suits_rainy"]) == (True, False, False)
    assert fields["visit_minutes"] == 180
    assert fields["temp_min"] is None and fields["latitude"] is None


def test_json_create_defaults_to_dry_weather():
    fields = clean_place({"name": "Primrose Hill", "category": "viewpoint"})
    assert (fields["suits_sunny"], fields["suits_cloudy"],
            fields["suits_rainy"]) == (True, True, False)
    assert fields["visit_minutes"] == 120


def test_json_update_changes_only_what_it_sends():
    fields = clean_place({"suits_rainy": True}, make_place())
    assert (fields["suits_sunny"], fields["suits_cloudy"],
            fields["suits_rainy"]) == (True, True, True)
    assert fields["name"] == "Hyde Park"


@pytest.mark.parametrize("data, message", [
    ({"category": "park"}, "Give the place a name."),
    ({"name": "x" * 61, "category": "park"}, "60 characters"),
    ({"name": "A", "category": "zoo"}, "Choose a category"),
    (dict(FORM, suits_sunny=None), "at least one kind of weather"),
    (dict(FORM, temp_min="20", temp_max="10"), "must not be above"),
    (dict(FORM, temp_min="hot"), "whole number"),
    (dict(FORM, temp_max="80"), "between -30 and 50"),
    (dict(FORM, visit_minutes="5"), "between 15 and 720"),
    (dict(FORM, latitude="51.5"), "needs both"),
    (dict(FORM, latitude="95", longitude="0"), "between -90 and 90"),
    (dict(FORM, notes="n" * 501), "500 characters"),
])
def test_bad_places_are_refused_with_a_reason(data, message):
    data = {k: v for k, v in data.items() if v is not None}
    with pytest.raises(ValueError, match=message):
        clean_place(data)


def test_a_pin_is_kept():
    fields = clean_place(dict(FORM, latitude="51.4787", longitude="-0.2956"))
    assert (fields["latitude"], fields["longitude"]) == (51.4787, -0.2956)


# ---------- CRUD, scoped to the owner ----------

def test_create_place_sets_the_owner(app, session):
    status, body = payload(create_place(FORM, OWNER))
    assert status == 201
    added = session.add.call_args[0][0]
    assert added.user_id == OWNER and added.name == "Kew Gardens"


def test_create_place_refuses_bad_data_without_touching_the_database(app, session):
    status, body = payload(create_place({"category": "park"}, OWNER))
    assert status == 400 and body["data"]["error"] == "Give the place a name."
    session.add.assert_not_called()


def test_someone_elses_place_is_not_found(app, session):
    session.get.return_value = make_place(user_id=OTHER)
    assert payload(get_place_by_id(3, OWNER))[0] == 404
    assert payload(update_place(3, {"name": "Mine now"}, OWNER))[0] == 404
    assert payload(delete_place(3, OWNER))[0] == 404
    session.delete.assert_not_called()


def test_update_own_place(app, session):
    place = make_place()
    session.get.return_value = place
    status, body = payload(update_place(3, {"name": "Hyde Park, Serpentine"}, OWNER))
    assert status == 200 and place.name == "Hyde Park, Serpentine"


def test_delete_own_place(app, session):
    place = make_place()
    session.get.return_value = place
    assert payload(delete_place(3, OWNER))[0] == 200
    session.delete.assert_called_once_with(place)


def test_bad_ids(app, session):
    assert payload(get_place_by_id("x", OWNER))[0] == 400


def test_database_failure_is_a_plain_500(app, session):
    session.get.side_effect = RuntimeError("connection refused")
    status, body = payload(get_place_by_id(3, OWNER))
    assert status == 500 and "connection" not in body["data"]["error"]


# ---------- Events made from a place ----------

EVENT = {"name": "Picnic", "start_time": "2026-10-17T11:00",
         "end_time": "2026-10-17T13:00", "location": "Hyde Park"}


def test_an_event_can_be_linked_to_an_own_place(app):
    with patch("database.db_event.Session") as s, \
         patch("database.db_event.owned_place", return_value=make_place()):
        status, body = payload(create_event(dict(EVENT, place_id=3), OWNER))
    added = s.return_value.__enter__.return_value.add.call_args[0][0]
    assert status == 201 and added.place_id == 3


def test_an_event_cannot_be_linked_to_someone_elses_place(app):
    with patch("database.db_event.Session") as s, \
         patch("database.db_event.owned_place", return_value=None):
        status, body = payload(create_event(dict(EVENT, place_id=3), OWNER))
    assert status == 400 and body["data"]["error"] == "That place wasn't found."
    s.return_value.__enter__.return_value.add.assert_not_called()
