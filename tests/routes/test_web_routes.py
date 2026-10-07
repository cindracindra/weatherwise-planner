"""Tests for the web pages and their forms, scoped to the current account."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app import create_app
from utils.response import StatusCode, build_response

USER = 7
EVENT = {
    "id": 5, "name": "Lunch with Sam",
    "start_time": "2025-12-06T12:30:00", "end_time": "2025-12-06T13:30:00",
    "location": "Borough Market",
}


def events():
    """A successful get_events() result (needs the app context)."""
    return build_response(StatusCode.OK, {"events": [EVENT]})


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client, app.app_context():
        with patch("routes.web_routes.current_user_id", return_value=USER), \
             patch("routes.web_routes.get_today_detail",
                   return_value={"year": 2025, "month": 12, "day": 6, "hour": 9}), \
             patch("routes.web_routes.get_full_calendar", return_value=[]), \
             patch("routes.web_routes.get_hourly_forecast_today", return_value=[]):
            yield client


# ---------- Home ----------

def test_homepage_shows_this_months_events(client):
    # One week holding the 6th, so the event has a day cell to appear in
    day = SimpleNamespace(day=6, weather=None, holidays=[])
    blank = SimpleNamespace(day=0, weather=None, holidays=[])
    week = SimpleNamespace(days=[blank] * 6 + [day])
    calendar = SimpleNamespace(weeks=[week])
    with patch("routes.web_routes.get_events", return_value=events()) as get, \
         patch("routes.web_routes.get_full_calendar", return_value=calendar):
        response = client.get("/")
    assert response.status_code == 200
    get.assert_called_once_with(USER, 2025, 12)
    assert b"Lunch with Sam" in response.data


def test_homepage_survives_a_database_error(client):
    failed = build_response(StatusCode.INTERNAL_SERVER_ERROR, {"error": "db down"})
    with patch("routes.web_routes.get_events", return_value=failed):
        response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Could not load events: db down" in response.data


def test_reload_redirects_home(client):
    response = client.get("/reload")
    assert response.status_code == 302
    assert response.location.endswith("/")


# ---------- Events page ----------

def test_events_page_lists_events(client):
    with patch("routes.web_routes.get_events", return_value=events()) as get:
        response = client.get("/management/event")
    assert response.status_code == 200
    get.assert_called_once_with(USER)
    assert b"Lunch with Sam" in response.data


def test_events_page_loads_selected_event(client):
    one = build_response(StatusCode.OK, EVENT)
    with patch("routes.web_routes.get_events", return_value=events()), \
         patch("routes.web_routes.get_event_by_id", return_value=one) as get_one:
        response = client.get("/management/event?selected_eventid=5")
    get_one.assert_called_once_with(5, USER)
    assert b"Change event" in response.data


def test_load_event_redirects_with_selection(client):
    response = client.post("/management/event/load", data={"eventid": "5"})
    assert response.status_code == 302
    assert "selected_eventid=5" in response.location


# ---------- Forms ----------

FORM = {"name": "Picnic", "start_time": "2026-10-18T12:00",
        "end_time": "15:00", "location": "Hyde Park"}


def test_create_event_for_current_user(client):
    created = build_response(StatusCode.CREATED, {"id": 9})
    with patch("routes.web_routes.create_event", return_value=created) as create:
        response = client.post("/management/event/create", data=FORM)
    assert "reqHttpCode=201" in response.location
    data, user = create.call_args[0]
    assert user == USER
    assert data["start_time"].hour == 12 and data["end_time"].hour == 15


def test_create_event_with_bad_time_does_not_crash(client):
    with patch("routes.web_routes.create_event") as create:
        response = client.post("/management/event/create",
                               data={**FORM, "start_time": ""})
    assert "reqHttpCode=400" in response.location
    create.assert_not_called()


def test_update_event_for_current_user(client):
    ok = build_response(StatusCode.OK, {"id": 5})
    with patch("routes.web_routes.update_event", return_value=ok) as update:
        response = client.post("/management/event/update",
                               data={**FORM, "eventid": "5"})
    assert "reqHttpCode=200" in response.location
    eventid, _, user = update.call_args[0]
    assert (eventid, user) == (5, USER)


def test_delete_event_for_current_user(client):
    ok = build_response(StatusCode.OK, {})
    with patch("routes.web_routes.delete_event", return_value=ok) as delete:
        response = client.post("/management/event/delete", data={"eventid": "5"})
    assert "reqHttpCode=200" in response.location
    delete.assert_called_once_with(5, USER)


def test_profile_pages_are_gone(client):
    assert client.get("/management/profile").status_code == 404
