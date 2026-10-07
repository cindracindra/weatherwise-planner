"""CSRF: form posts need the hidden token from one of our own pages.

Here CSRF protection stays on (other test files switch it off)."""

import re
from unittest.mock import patch

import pytest

from app import create_app
from utils.response import StatusCode, build_response

USER = 7
FORM = {"name": "Picnic", "start_time": "2026-10-18T12:00",
        "end_time": "15:00", "location": "Hyde Park"}


def make_client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["LOGIN_DISABLED"] = True
    return app.test_client()


@pytest.fixture
def client():
    with make_client() as client, client.application.app_context(), \
         patch("routes.web_routes.current_user_id", return_value=USER), \
         patch("routes.api_routes.current_user_id", return_value=USER), \
         patch("routes.web_routes.get_events",
               side_effect=lambda *a: build_response(StatusCode.OK,
                                                     {"events": []})):
        yield client


def token_from(client):
    """The token our own Events page puts in its forms."""
    html = client.get("/management/event").get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def test_forged_form_is_refused(client):
    with patch("routes.web_routes.delete_event") as delete:
        response = client.post("/management/event/delete", data={"eventid": "12"},
                               headers={"Referer": "https://evil.example/"})
    delete.assert_not_called()
    assert response.status_code == 302
    assert "evil.example" not in response.location
    with client.session_transaction() as session:
        assert ("error", "That form had expired. Please try again.") in \
            session["_flashes"]


def test_token_from_another_session_is_refused(client):
    with make_client() as other:
        stolen = token_from(other)
    with patch("routes.web_routes.create_event") as create:
        client.post("/management/event/create",
                    data={**FORM, "csrf_token": stolen})
    create.assert_not_called()


def test_our_own_form_is_accepted(client):
    created = build_response(StatusCode.CREATED, {"id": 9})
    with patch("routes.web_routes.create_event", return_value=created) as create:
        response = client.post("/management/event/create",
                               data={**FORM, "csrf_token": token_from(client)})
    create.assert_called_once()
    assert "reqHttpCode=201" in response.location


def test_sign_out_needs_the_token_too(client):
    response = client.post("/logout")
    with client.session_transaction() as session:
        assert ("error", "That form had expired. Please try again.") in \
            session["_flashes"]
    assert response.status_code == 302


def test_json_api_works_without_a_token(client):
    created = build_response(StatusCode.CREATED, {"id": 9})
    with patch("routes.api_routes.create_event", return_value=created):
        response = client.post("/api/events", json={
            "name": "Picnic", "start_time": "2026-10-18T12:00:00",
            "end_time": "2026-10-18T15:00:00", "location": "Hyde Park"})
    assert response.status_code == 201


def test_every_form_carries_a_token(client):
    html = client.get("/management/event").get_data(as_text=True)
    forms = re.findall(r'<form\b[^>]*method="post".*?</form>', html, re.S)
    assert forms
    assert all('name="csrf_token"' in form for form in forms)
