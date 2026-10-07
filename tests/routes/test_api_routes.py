"""Tests for the REST API: every endpoint works on the current account."""

from unittest.mock import patch

import pytest

from app import create_app
from utils.response import StatusCode, build_response

USER = 7


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["LOGIN_DISABLED"] = True  # sign-in is covered in test_auth.py
    app.config["WTF_CSRF_ENABLED"] = False  # covered in test_csrf.py
    with app.test_client() as client, app.app_context():
        with patch("routes.api_routes.current_user_id", return_value=USER):
            yield client


def ok(data=None):
    return build_response(StatusCode.OK, data or {})


def test_get_events_for_current_user(client):
    with patch("routes.api_routes.get_events", return_value=ok({"events": []})) as get:
        response = client.get("/api/events")
    assert response.status_code == 200
    get.assert_called_once_with(USER)


def test_get_event_by_id_for_current_user(client):
    with patch("routes.api_routes.get_event_by_id", return_value=ok()) as get:
        client.get("/api/events/5")
    get.assert_called_once_with(5, USER)


def test_create_event_for_current_user(client):
    body = {"name": "Picnic", "start_time": "2026-10-18T12:00:00",
            "end_time": "2026-10-18T15:00:00", "location": "Hyde Park"}
    created = build_response(StatusCode.CREATED, {"id": 1})
    with patch("routes.api_routes.create_event", return_value=created) as create:
        response = client.post("/api/events", json=body)
    assert response.status_code == 201
    create.assert_called_once_with(body, USER)


def test_update_event_for_current_user(client):
    with patch("routes.api_routes.update_event", return_value=ok()) as update:
        client.patch("/api/events/5", json={"name": "Long picnic"})
    update.assert_called_once_with(5, {"name": "Long picnic"}, USER)


def test_delete_event_for_current_user(client):
    with patch("routes.api_routes.delete_event", return_value=ok()) as delete:
        client.delete("/api/events/5")
    delete.assert_called_once_with(5, USER)


@pytest.mark.parametrize("path", ["/api/profiles", "/api/eventxprofiles"])
def test_profile_endpoints_are_gone(client, path):
    assert client.get(path).status_code == 404
