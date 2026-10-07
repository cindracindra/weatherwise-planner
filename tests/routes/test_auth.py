"""Tests for sign-in: protected pages, the API's 401, the local developer
sign-in, sign-out, and the ?next= redirect check."""

from unittest.mock import patch

import pytest

from app import create_app
from models.db_models.user import AppUser
from utils.auth import is_safe_next, login_manager

DEV = AppUser(id=42, google_sub="local-dev", name="Local developer")


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture
def dev_client(app):
    """A client with the local developer sign-in switched on, and the
    database calls it makes replaced by the DEV account."""
    app.config["DEV_LOGIN"] = True
    load = lambda user_id: DEV if user_id == "42" else None  # noqa: E731
    with app.test_client() as client, \
         patch("routes.auth_routes.get_or_create_dev_user", return_value=DEV), \
         patch.object(login_manager, "_user_callback", load):
        yield client


# ---------- Signed out ----------

def test_pages_redirect_to_sign_in(client):
    response = client.get("/management/event")
    assert response.status_code == 302
    assert "/login?next=/management/event" in response.location


def test_api_answers_401_as_json(client):
    response = client.get("/api/events")
    assert response.status_code == 401
    assert response.get_json()["statusMessage"] == "UNAUTHORIZED"


def test_sign_in_page_is_open(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in with Google" in response.data


def test_dev_sign_in_is_off_by_default(client):
    assert b"Continue as local developer" not in client.get("/login").data
    assert client.post("/login/dev").status_code == 404


def test_dev_sign_in_is_never_on_render(app, monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    app.config["DEV_LOGIN"] = True
    with app.test_client() as client:
        assert client.post("/login/dev").status_code == 404


# ---------- Signing in and out ----------

def test_dev_sign_in_sets_a_lasting_session(dev_client):
    response = dev_client.post("/login/dev", data={"next": "/management/event"})
    assert response.status_code == 302
    assert response.location.endswith("/management/event")
    with dev_client.session_transaction() as session:
        assert session["_user_id"] == "42"
        assert session.permanent is True


def test_signed_in_user_reaches_the_api(dev_client):
    dev_client.post("/login/dev")
    with patch("routes.api_routes.get_events") as get_events:
        get_events.return_value = ({"events": []}, 200)
        response = dev_client.get("/api/events")
    assert response.status_code == 200
    get_events.assert_called_once_with(42)


def test_sign_out_ends_the_session(dev_client):
    dev_client.post("/login/dev")
    response = dev_client.post("/logout")
    assert response.location.endswith("/login")
    with dev_client.session_transaction() as session:
        assert "_user_id" not in session
    assert dev_client.get("/api/events").status_code == 401


def test_sign_out_needs_a_post(dev_client):
    assert dev_client.get("/logout").status_code == 405


def test_unsafe_next_goes_home_instead(dev_client):
    response = dev_client.post("/login/dev", data={"next": "https://evil.example/"})
    assert response.location.endswith("/")
    assert "evil.example" not in response.location


# ---------- The ?next= check ----------

@pytest.mark.parametrize("target, safe", [
    ("/management/event", True),
    ("/?a=1", True),
    ("", False),
    (None, False),
    ("https://evil.example/", False),
    ("//evil.example/", False),
    ("/\\evil.example/", False),
    ("javascript:alert(1)", False),
])
def test_is_safe_next(target, safe):
    assert is_safe_next(target) is safe


# ---------- Cookie settings ----------

def test_session_cookie_settings(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["PERMANENT_SESSION_LIFETIME"].days == 30
    assert app.secret_key and app.secret_key != "event-calendar"
