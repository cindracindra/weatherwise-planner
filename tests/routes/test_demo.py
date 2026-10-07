"""Tests for "Try the demo": throwaway accounts with sample events."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from models.db_models.user import AppUser
from utils.auth import login_manager
from utils.response import StatusCode, build_response
from utils.demo import (
    DEMO_CAP, DEMO_LIFETIME, SAMPLE_EVENTS, DemoFull, cleanup_demo_users, create_demo_user,
    delete_demo_user, sample_events,
)

DEMO = AppUser(id=11, name="Demo visitor", is_demo=True)
REAL = AppUser(id=3, google_sub="g-1", name="Cindra Tan", is_demo=False)
TODAY = {"year": 2026, "month": 10, "day": 7, "hour": 9}


def sql(statement):
    """The statement's SQL, with values filled in where SQLAlchemy can
    print them (it can't print an interval like '1 day'; that one stays a
    placeholder here and is sent to Postgres as a parameter)."""
    try:
        return str(statement.compile(compile_kwargs={"literal_binds": True}))
    except Exception:
        return str(statement.compile())


def statement_params(statement):
    return list(statement.compile().params.values())


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # covered in test_csrf.py
    users = {"11": DEMO, "3": REAL}
    with app.test_client() as client, \
         patch.object(login_manager, "_user_callback", users.get):
        yield client


# ---------- Signing in and out ----------

def test_try_the_demo_signs_in_a_fresh_account(client):
    with patch("routes.auth_routes.create_demo_user", return_value=DEMO) as create:
        response = client.post("/login/demo")
    create.assert_called_once()
    assert response.location.endswith("/")
    with client.session_transaction() as session:
        assert session["_user_id"] == "11"
        assert session.permanent is False  # ends when the browser closes


def test_sign_in_page_offers_the_demo(client):
    assert b"Try the demo" in client.get("/login").data


def test_signing_out_of_a_demo_deletes_it(client):
    with patch("routes.auth_routes.create_demo_user", return_value=DEMO):
        client.post("/login/demo")
    with patch("routes.auth_routes.delete_demo_user") as delete:
        client.post("/logout")
    delete.assert_called_once_with(11)
    assert b"The demo calendar is deleted." in client.get("/login").data


def test_signing_out_of_a_real_account_deletes_nothing(client):
    with client.session_transaction() as session:
        session["_user_id"] = "3"
    with patch("routes.auth_routes.delete_demo_user") as delete:
        client.post("/logout")
    delete.assert_not_called()


def test_demo_banner_shows_only_for_demo_accounts(client):
    # The home page, with its database and weather calls stubbed out
    with client.application.app_context():
        no_events = build_response(StatusCode.OK, {"events": []})
    with patch("routes.web_routes.get_events", return_value=no_events), \
         patch("routes.web_routes.get_today_detail", return_value=TODAY), \
         patch("routes.web_routes.get_full_calendar", return_value=[]), \
         patch("routes.web_routes.get_hourly_forecast_today", return_value=[]):
        with client.session_transaction() as session:
            session["_user_id"] = "11"
        assert b"exploring a demo calendar" in client.get("/").data
        with client.session_transaction() as session:
            session["_user_id"] = "3"
        assert b"exploring a demo calendar" not in client.get("/").data


# ---------- Sample events ----------

def test_sample_events_sit_around_today():
    with patch("utils.demo.get_today_detail", return_value=TODAY):
        events = sample_events(user_id=11)
    assert len(events) == len(SAMPLE_EVENTS)
    assert all(e.user_id == 11 for e in events)
    assert all(e.end_time > e.start_time for e in events)
    days = {e.start_time.date() for e in events}
    assert datetime(2026, 10, 7).date() in days          # something today
    assert min(days) < datetime(2026, 10, 7).date() < max(days)


# ---------- Creating and tidying up ----------

@pytest.fixture
def db():
    with patch("utils.demo.Session") as session_class:
        session = session_class.return_value.__enter__.return_value
        session.execute.return_value.scalar_one.return_value = 0

        def flush():
            for call in session.add.call_args_list:
                call[0][0].id = 11
        session.flush.side_effect = flush
        yield session


def test_create_demo_user_makes_a_marked_account_with_events(db):
    with patch("utils.demo.get_today_detail", return_value=TODAY):
        user = create_demo_user()
    added = db.add.call_args[0][0]
    assert added is user and user.is_demo is True
    events = db.add_all.call_args[0][0]
    assert len(events) == len(SAMPLE_EVENTS)
    assert all(e.user_id == 11 for e in events)
    db.commit.assert_called_once()


def test_cleanup_removes_demos_older_than_a_day_by_the_db_clock():
    session = MagicMock()
    session.execute.return_value.scalar_one.return_value = 5
    assert cleanup_demo_users(session) == 5
    first = sql(session.execute.call_args_list[0][0][0])
    assert first.startswith("DELETE FROM app_user")
    assert "app_user.is_demo" in first
    assert "app_user.created_at < now() -" in first
    assert statement_params(session.execute.call_args_list[0][0][0]) == [
        DEMO_LIFETIME]


def test_no_new_demo_at_the_cap_and_nobody_is_evicted(db):
    db.execute.return_value.scalar_one.return_value = DEMO_CAP
    with pytest.raises(DemoFull):
        create_demo_user()
    db.add.assert_not_called()
    deletes = [sql(c[0][0]) for c in db.execute.call_args_list
               if sql(c[0][0]).startswith("DELETE")]
    assert len(deletes) == 1 and "created_at <" in deletes[0]


def test_busy_demo_shows_a_message(client):
    with patch("routes.auth_routes.create_demo_user", side_effect=DemoFull):
        response = client.post("/login/demo")
    assert response.location.endswith("/login")
    assert b"The demo is busy right now" in client.get("/login").data


def test_delete_demo_user_never_touches_real_accounts():
    with patch("utils.demo.Session") as session_class:
        session = session_class.return_value.__enter__.return_value
        delete_demo_user(3)
    statement = sql(session.execute.call_args[0][0])
    assert "app_user.id = 3" in statement and "app_user.is_demo" in statement
