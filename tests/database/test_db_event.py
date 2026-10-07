"""Tests for database/db_event.py: CRUD scoped to the owning account."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from database.db_event import (
    _month_bounds,
    create_event,
    delete_event,
    get_event_by_id,
    get_events,
    update_event,
)
from models.db_models.event import Event

OWNER, OTHER = 7, 8


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        yield app


@pytest.fixture
def session():
    """The SQLAlchemy session db_event opens, as a mock."""
    with patch("database.db_event.Session") as session_class:
        yield session_class.return_value.__enter__.return_value


def make_event(user_id=OWNER, **overrides):
    event = MagicMock(spec=Event)
    event.id = overrides.get("id", 1)
    event.name = overrides.get("name", "Picnic")
    event.start_time = overrides.get("start_time", datetime(2026, 10, 18, 12, 0))
    event.end_time = overrides.get("end_time", datetime(2026, 10, 18, 15, 0))
    event.location = overrides.get("location", "Hyde Park")
    event.user_id = user_id
    return event


def payload(result):
    response, status = result
    return status, response.get_json()


# ---------- get_events ----------

def test_get_events_returns_serialized_events(app, session):
    session.execute.return_value.scalars.return_value.all.return_value = [make_event()]

    status, body = payload(get_events(OWNER))

    assert status == 200
    assert body["data"]["events"][0]["name"] == "Picnic"
    assert body["data"]["events"][0]["start_time"] == "2026-10-18T12:00:00"


def test_get_events_filters_by_owner(app, session):
    session.execute.return_value.scalars.return_value.all.return_value = []

    get_events(OWNER, 2026, 10)

    stmt = session.execute.call_args[0][0]
    sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "event.user_id = 7" in sql
    assert "2026-10-01" in sql and "2026-11-01" in sql


def test_month_bounds_wraps_december():
    assert _month_bounds(2026, 12) == (datetime(2026, 12, 1), datetime(2027, 1, 1))


# ---------- get_event_by_id ----------

def test_get_own_event(app, session):
    session.get.return_value = make_event()
    status, body = payload(get_event_by_id(1, OWNER))
    assert status == 200
    assert body["data"]["name"] == "Picnic"


def test_get_someone_elses_event_is_not_found(app, session):
    session.get.return_value = make_event(user_id=OTHER)
    status, _ = payload(get_event_by_id(1, OWNER))
    assert status == 404


def test_get_event_bad_id(app, session):
    status, _ = payload(get_event_by_id("abc", OWNER))
    assert status == 400


# ---------- create_event ----------

def test_create_event_sets_owner(app, session):
    result = create_event(
        {"name": "Picnic", "start_time": "2026-10-18T12:00:00",
         "end_time": "2026-10-18T15:00:00", "location": "Hyde Park"},
        OWNER,
    )
    added = session.add.call_args[0][0]
    assert added.user_id == OWNER
    assert result[1] == 201


def test_create_event_missing_fields(app, session):
    status, body = payload(create_event({"name": "Picnic"}, OWNER))
    assert status == 400
    assert "start_time" in body["data"]["error"]
    session.add.assert_not_called()


def test_create_event_end_before_start(app, session):
    status, _ = payload(create_event(
        {"name": "Picnic", "start_time": "2026-10-18T15:00:00",
         "end_time": "2026-10-18T12:00:00", "location": "Hyde Park"},
        OWNER,
    ))
    assert status == 400


# ---------- update_event ----------

def test_update_own_event(app, session):
    event = make_event()
    session.get.return_value = event
    status, _ = payload(update_event(1, {"name": "Long picnic"}, OWNER))
    assert status == 200
    assert event.name == "Long picnic"
    session.commit.assert_called_once()


def test_update_someone_elses_event_is_not_found(app, session):
    event = make_event(user_id=OTHER)
    session.get.return_value = event
    status, _ = payload(update_event(1, {"name": "Hijacked"}, OWNER))
    assert status == 404
    assert event.name == "Picnic"
    session.commit.assert_not_called()


# ---------- delete_event ----------

def test_delete_own_event(app, session):
    event = make_event()
    session.get.return_value = event
    status, _ = payload(delete_event(1, OWNER))
    assert status == 200
    session.delete.assert_called_once_with(event)


def test_delete_someone_elses_event_is_not_found(app, session):
    session.get.return_value = make_event(user_id=OTHER)
    status, _ = payload(delete_event(1, OWNER))
    assert status == 404
    session.delete.assert_not_called()


# ---------- Things a client can't do ----------

def test_update_cannot_change_the_owner(app, session):
    event = make_event()
    session.get.return_value = event
    update_event(1, {"name": "Picnic", "user_id": OTHER}, OWNER)
    assert event.user_id == OWNER


def test_create_ignores_a_user_id_in_the_request(app, session):
    create_event(
        {"name": "Picnic", "start_time": "2026-10-18T12:00:00",
         "end_time": "2026-10-18T15:00:00", "location": "Hyde Park",
         "user_id": OTHER},
        OWNER,
    )
    assert session.add.call_args[0][0].user_id == OWNER


def test_unexpected_errors_do_not_reach_the_browser(app, session):
    session.execute.side_effect = RuntimeError(
        "connection to server at 10.0.0.5 failed: password authentication")
    status, body = payload(get_events(OWNER))
    assert status == 500
    assert "10.0.0.5" not in body["data"]["error"]
    assert "password" not in body["data"]["error"]
