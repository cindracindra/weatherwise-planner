"""Tests for sign-in: protected pages, the API's 401, the local developer
sign-in, sign-out, and the ?next= redirect check."""

from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from models.db_models.user import AppUser
from utils.auth import is_safe_next, login_manager, upsert_google_user

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


# ---------- Google sign-in (Google itself is replaced by a stand-in) ----------

GOOGLE_USER = AppUser(id=5, google_sub="g-123", email="cindra@example.com",
                      name="Cindra")
VERIFIED = {"sub": "g-123", "email": "cindra@example.com",
            "email_verified": True, "name": "Cindra"}


@pytest.fixture
def google(app):
    """A stand-in for Google's OAuth client."""
    from flask import redirect as flask_redirect
    fake = MagicMock()
    fake.authorize_redirect.side_effect = lambda uri: flask_redirect(
        "https://accounts.google.com/o/oauth2/auth?redirect_uri=" + uri)
    load = lambda user_id: GOOGLE_USER if user_id == "5" else None  # noqa: E731
    with patch("routes.auth_routes.google_client", return_value=fake), \
         patch.object(login_manager, "_user_callback", load):
        yield fake


def test_google_button_links_to_google_sign_in(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    with create_app().test_client() as client:
        body = client.get("/login?next=/management/event").data
    assert b'href="/login/google?next=/management/event"' in body


def test_google_sign_in_is_off_without_credentials(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    with create_app().test_client() as client:
        assert b"isn't set up here" in client.get("/login").data
        assert client.get("/login/google").status_code == 404
        assert client.get("/auth/google/callback").status_code == 404


def test_login_google_sends_you_to_google(client, google):
    response = client.get("/login/google?next=/management/event")
    assert response.location.startswith("https://accounts.google.com/")
    google.authorize_redirect.assert_called_once_with(
        "http://localhost/auth/google/callback")
    with client.session_transaction() as session:
        assert session["next"] == "/management/event"


def test_login_google_drops_an_unsafe_next(client, google):
    client.get("/login/google?next=https://evil.example/")
    with client.session_transaction() as session:
        assert session["next"] is None


def test_google_callback_signs_you_in(client, google):
    google.authorize_access_token.return_value = {"userinfo": VERIFIED}
    with client.session_transaction() as session:
        session["next"] = "/management/event"
    with patch("routes.auth_routes.upsert_google_user",
               return_value=GOOGLE_USER) as upsert:
        response = client.get("/auth/google/callback?code=abc&state=xyz")
    upsert.assert_called_once_with(VERIFIED)
    assert response.location.endswith("/management/event")
    with client.session_transaction() as session:
        assert session["_user_id"] == "5"
        assert session.permanent is True
        assert "next" not in session


def test_google_callback_when_cancelled(client, google):
    response = client.get("/auth/google/callback?error=access_denied")
    assert response.location.endswith("/login")
    google.authorize_access_token.assert_not_called()
    assert b"Sign-in was cancelled." in client.get("/login").data


def test_google_callback_rejects_a_bad_reply(client, google):
    from authlib.integrations.base_client import OAuthError
    google.authorize_access_token.side_effect = OAuthError("mismatching_state")
    with patch("routes.auth_routes.upsert_google_user") as upsert:
        response = client.get("/auth/google/callback?code=abc&state=forged")
    assert response.location.endswith("/login")
    upsert.assert_not_called()
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_google_callback_needs_a_verified_email(client, google):
    google.authorize_access_token.return_value = {
        "userinfo": {**VERIFIED, "email_verified": False}}
    with patch("routes.auth_routes.upsert_google_user") as upsert:
        response = client.get("/auth/google/callback?code=abc&state=xyz")
    assert response.location.endswith("/login")
    upsert.assert_not_called()


# ---------- Finding or creating the account ----------

@pytest.fixture
def db():
    with patch("utils.auth.Session") as session_class:
        yield session_class.return_value.__enter__.return_value


def test_first_google_sign_in_creates_the_account(db):
    db.execute.return_value.scalar_one_or_none.return_value = None
    user = upsert_google_user(VERIFIED)
    added = db.add.call_args[0][0]
    assert (added.google_sub, added.email, added.name) == (
        "g-123", "cindra@example.com", "Cindra")
    assert user is added


def test_later_sign_ins_refresh_name_and_email(db):
    existing = AppUser(id=5, google_sub="g-123", email="old@example.com",
                       name="Old name")
    db.execute.return_value.scalar_one_or_none.return_value = existing
    upsert_google_user(VERIFIED)
    db.add.assert_not_called()
    assert (existing.email, existing.name) == ("cindra@example.com", "Cindra")


# ---------- Every data route is protected ----------

def test_every_page_and_api_route_needs_sign_in(app):
    """Walks every route in the app, so a page added later without
    sign-in fails here. Only the sign-in pages and static files are open."""
    open_routes = {"auth", "static"}
    checked = 0
    with app.test_client() as client:
        for rule in app.url_map.iter_rules():
            area = rule.endpoint.split(".")[0]
            if area in open_routes:
                continue
            url = rule.rule.replace("<int:eventid>", "1")
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                response = client.open(url, method=method)
                assert response.status_code in (302, 401), (method, url)
                if response.status_code == 302:
                    assert "/login" in response.location, (method, url)
                checked += 1
    assert checked >= 12
