import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from database.db_event import get_events, get_event_by_id, create_event, update_event, delete_event
from models.db_models.event import Event
from datetime import datetime


@pytest.fixture
def app():
    """Create application context for tests."""
    app = create_app()
    app.config['TESTING'] = True
    return app


# Test get_events

def test_get_events(app):
    with app.app_context():
        mock_event = MagicMock(spec=Event)
        mock_event.id = 1
        mock_event.name = "Test Event"
        mock_event.start_time = datetime(2025, 12, 1, 10, 0)
        mock_event.end_time = datetime(2025, 12, 1, 12, 0)
        mock_event.location = "Test Location"

        # Patch the Session context manager
        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = [mock_event]

            response, status = get_events()
            result = response.get_json()
            assert result["statusCode"] == 200
            assert result["statusMessage"] == "SUCCESS"
            assert "events" in result["data"]
            assert len(result["data"]["events"]) == 1
            assert result["data"]["events"][0]["name"] == "Test Event"


def test_get_event_by_id_success(app):
    with app.app_context():
        mock_event_instance = MagicMock(spec=Event)
        mock_event_instance.id = 1
        mock_event_instance.name = "Event 1"
        mock_event_instance.start_time = datetime(2025, 12, 1, 10, 0)
        mock_event_instance.end_time = datetime(2025, 12, 1, 12, 0)
        mock_event_instance.location = "Location 1"

        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = mock_event_instance

            response, status = get_event_by_id(1)
            result = response.get_json()
            assert status == 200
            assert result["data"]["id"] == 1
            assert result["data"]["name"] == "Event 1"

def test_get_event_by_id_not_found(app):
    with app.app_context():
        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = None

            response, status = get_event_by_id(999)
            result = response.get_json()
            assert status == 404
            assert "not found" in result["data"]["error"]

def test_get_event_by_id_invalid(app):
    with app.app_context():
        response, status = get_event_by_id("abc")
        result = response.get_json()
        assert status == 400
        assert "must be an integer" in result["data"]["error"]

# Test create_event

def test_create_event_success(app):
    with app.app_context():
        data = {
            "name": "New Event",
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T12:00:00",
            "location": "New Location",
        }

        mock_event_instance = MagicMock(spec=Event)
        mock_event_instance.id = 1
        mock_event_instance.name = data["name"]
        mock_event_instance.start_time = datetime.fromisoformat(data["start_time"])
        mock_event_instance.end_time = datetime.fromisoformat(data["end_time"])
        mock_event_instance.location = data["location"]

        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.side_effect = lambda e: setattr(e, "id", 1)
            # Patch Event constructor to return our mock instance
            with patch("database.db_event.Event", return_value=mock_event_instance):
                response, status = create_event(data)
                result = response.get_json()
                assert status == 201
                assert result["statusCode"] == 201
                assert result["statusMessage"] == "CREATED"
                assert result["data"]["id"] == 1
                assert result["data"]["name"] == "New Event"

def test_create_event_missing_fields(app):
    with app.app_context():
        data = {"name": "No Location"}
        response, status = create_event(data)
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "Missing required fields" in result["data"]["error"]

def test_create_event_invalid_datetime(app):
    with app.app_context():
        data = {
            "name": "Bad Event",
            "start_time": "invalid-date",
            "end_time": "2025-12-01T12:00:00",
            "location": "Somewhere",
        }
        response, status = create_event(data)
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "Invalid datetime format for 'start_time'" in result["data"]["error"]

def test_create_event_end_before_start(app):
    with app.app_context():
        data = {
            "name": "Backwards Event",
            "start_time": "2025-12-01T12:00:00",
            "end_time": "2025-12-01T10:00:00",
            "location": "Somewhere",
        }
        response, status = create_event(data)
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "End time must be after start time" in result["data"]["error"]


# Test delete_event

def test_delete_event_success(app):
    with app.app_context():
        mock_event_instance = MagicMock(spec=Event)

        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = mock_event_instance
            mock_session.delete.return_value = None
            mock_session.commit.return_value = None

            response, status = delete_event(1)
            result = response.get_json()
            assert status == 200
            assert result["statusCode"] == 200
            assert result["statusMessage"] == "SUCCESS"
            assert "deleted" in result["data"]["message"]

def test_delete_event_not_found(app):
    with app.app_context():
        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = None

            response, status = delete_event(999)
            result = response.get_json()
            assert status == 404
            assert result["statusCode"] == 404
            assert result["statusMessage"] == "NOT_FOUND"
            assert "not found" in result["data"]["error"]

def test_delete_event_invalid_id(app):
    with app.app_context():
        response, status = delete_event("abc")
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "must be an integer" in result["data"]["error"]


# Test update_event

def test_update_event_success(app):
    with app.app_context():
        mock_event_instance = MagicMock(spec=Event)
        mock_event_instance.id = 1
        mock_event_instance.name = "Old Name"
        mock_event_instance.start_time = datetime(2025, 12, 1, 10, 0)
        mock_event_instance.end_time = datetime(2025, 12, 1, 12, 0)
        mock_event_instance.location = "Old Location"

        update_data = {"name": "New Name", "location": "New Location"}

        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = mock_event_instance
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None

            response, status = update_event(1, update_data)
            result = response.get_json()
            assert status == 200
            assert result["data"]["name"] == "New Name"
            assert result["data"]["location"] == "New Location"

def test_update_event_invalid_id(app):
    with app.app_context():
        response, status = update_event("abc", {"name": "Test"})
        result = response.get_json()
        assert status == 400
        assert "must be an integer" in result["data"]["error"]

def test_update_event_not_found(app):
    with app.app_context():
        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = None

            response, status = update_event(999, {"name": "Test"})
            result = response.get_json()
            assert status == 404
            assert "not found" in result["data"]["error"]

def test_update_event_invalid_datetime(app):
    with app.app_context():
        mock_event_instance = MagicMock(spec=Event)
        mock_event_instance.id = 1
        mock_event_instance.start_time = datetime(2025, 12, 1, 10, 0)
        mock_event_instance.end_time = datetime(2025, 12, 1, 12, 0)

        update_data = {"start_time": "invalid-date"}

        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = mock_event_instance

            response, status = update_event(1, update_data)
            result = response.get_json()
            assert status == 400
            assert "Invalid datetime format" in result["data"]["error"]

def test_update_event_end_before_start(app):
    with app.app_context():
        mock_event_instance = MagicMock(spec=Event)
        mock_event_instance.id = 1
        mock_event_instance.start_time = datetime(2025, 12, 1, 10, 0)
        mock_event_instance.end_time = datetime(2025, 12, 1, 12, 0)

        update_data = {"start_time": "2025-12-01T14:00:00"}

        with patch("database.db_event.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = mock_event_instance

            response, status = update_event(1, update_data)
            result = response.get_json()
            assert status == 400
            assert "End time must be after start time" in result["data"]["error"]