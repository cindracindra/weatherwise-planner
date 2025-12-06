"""Tests for database.db_composite module."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from database.db_composite import (
    get_events_by_profile_id,
    get_events_by_profile_id_by_month,
    create_event_and_profile_association,
    delete_event_and_profile_association
)
from models.db_models.event import Event
from models.db_models.eventxprofile import EventXProfile
from app import create_app


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def mock_event():
    """Create a mock Event object."""
    mock = MagicMock(spec=Event)
    mock.id = 1
    mock.name = "Test Event"
    mock.start_time = datetime(2025, 12, 10, 10, 0, 0)
    mock.end_time = datetime(2025, 12, 10, 12, 0, 0)
    mock.location = "Test Location"
    return mock


@pytest.fixture
def mock_eventxprofile():
    """Create a mock EventXProfile object."""
    mock = MagicMock(spec=EventXProfile)
    mock.id = 1
    mock.eventid = 1
    mock.profileid = 1
    return mock


# ========== Tests for get_events_by_profile_id ==========

def test_get_events_by_profile_id_success(app, mock_event):
    """Test get_events_by_profile_id returns events successfully."""
    with app.app_context():
        with patch("database.db_composite.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = [mock_event]

            response, status = get_events_by_profile_id(1)
            result = response.get_json()
            
            assert status == 200
            assert result["statusCode"] == 200
            assert result["statusMessage"] == "SUCCESS"
            assert "events" in result["data"]
            assert len(result["data"]["events"]) == 1


def test_get_events_by_profile_id_empty(app):
    """Test get_events_by_profile_id with no events."""
    with app.app_context():
        with patch("database.db_composite.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = []

            response, status = get_events_by_profile_id(1)
            result = response.get_json()
            
            assert status == 200
            assert result["data"]["events"] == []


# ========== Tests for get_events_by_profile_id_by_month ==========

def test_get_events_by_profile_id_by_month_success(app, mock_event):
    """Test get_events_by_profile_id_by_month returns filtered events."""
    with app.app_context():
        with patch("database.db_composite.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = [mock_event]

            response, status = get_events_by_profile_id_by_month(1, 2025, 12)
            result = response.get_json()
            
            assert status == 200
            assert result["statusCode"] == 200
            assert "events" in result["data"]


def test_get_events_by_profile_id_by_month_empty(app):
    """Test get_events_by_profile_id_by_month with no matching events."""
    with app.app_context():
        with patch("database.db_composite.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = []

            response, status = get_events_by_profile_id_by_month(1, 2025, 1)
            result = response.get_json()
            
            assert status == 200
            assert result["data"]["events"] == []


# ========== Tests for create_event_and_profile_association ==========

def test_create_event_and_profile_association_success(app, mock_event, mock_eventxprofile):
    """Test create_event_and_profile_association creates both successfully."""
    with app.app_context():
        start_time = datetime(2025, 12, 10, 10, 0, 0)
        end_time = datetime(2025, 12, 10, 12, 0, 0)

        with patch("database.db_composite.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            
            with patch("database.db_composite.Event", return_value=mock_event):
                with patch("database.db_composite.EventXProfile", return_value=mock_eventxprofile):
                    response, status = create_event_and_profile_association(
                        "Test Event",
                        start_time,
                        end_time,
                        "Test Location",
                        1
                    )
                    result = response.get_json()
                    
                    assert status == 201
                    assert result["statusCode"] == 201
                    assert result["statusMessage"] == "CREATED"
                    assert "event" in result["data"]
                    assert "eventxprofile" in result["data"]


def test_create_event_and_profile_association_database_error(app):
    """Test create_event_and_profile_association handles database errors."""
    with app.app_context():
        start_time = datetime(2025, 12, 10, 10, 0, 0)
        end_time = datetime(2025, 12, 10, 12, 0, 0)

        with patch("database.db_composite.Session") as mock_session_class:
            mock_session_class.return_value.__enter__.side_effect = Exception("Database error")

            response, status = create_event_and_profile_association(
                "Test Event",
                start_time,
                end_time,
                "Test Location",
                1
            )
            result = response.get_json()
            
            assert status == 500
            assert result["statusCode"] == 500
            assert "error" in result["data"]


# ========== Tests for delete_event_and_profile_association ==========

def test_delete_event_and_profile_association_success(app, mock_event, mock_eventxprofile):
    """Test delete_event_and_profile_association deletes successfully."""
    with app.app_context():
        with patch("database.db_composite.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = mock_event
            mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_eventxprofile]

            response, status = delete_event_and_profile_association(1)
            result = response.get_json()
            
            assert status == 200
            assert result["statusCode"] == 200
            assert "deleted_event" in result["data"]
            assert "deleted_eventxprofiles" in result["data"]
            assert "count" in result["data"]


def test_delete_event_and_profile_association_not_found(app):
    """Test delete_event_and_profile_association with non-existent event."""
    with app.app_context():
        with patch("database.db_composite.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = None

            response, status = delete_event_and_profile_association(999)
            result = response.get_json()
            
            assert status == 404
            assert result["statusCode"] == 404
            assert "not found" in result["data"]["error"]


def test_delete_event_and_profile_association_database_error(app):
    """Test delete_event_and_profile_association handles database errors."""
    with app.app_context():
        with patch("database.db_composite.Session") as mock_session_class:
            mock_session_class.return_value.__enter__.side_effect = Exception("Database error")

            response, status = delete_event_and_profile_association(1)
            result = response.get_json()
            
            assert status == 500
            assert result["statusCode"] == 500
            assert "error" in result["data"]
