import pytest
from unittest.mock import patch, MagicMock
from database.event import get_events, create_event, delete_event
from models.db_models.event import Event
from datetime import datetime


# Test get_events

def test_get_events():
    mock_event = MagicMock(spec=Event)
    mock_event.id = 1
    mock_event.name = "Test Event"
    mock_event.start_time = datetime(2025, 12, 1, 10, 0)
    mock_event.end_time = datetime(2025, 12, 1, 12, 0)
    mock_event.location = "Test Location"

    # Patch the Session context manager
    with patch("database.event.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = [mock_event]

        result = get_events()
        assert "events" in result
        assert len(result["events"]) == 1
        assert result["events"][0]["name"] == "Test Event"


# Test create_event

def test_create_event_success():
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

    with patch("database.event.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda e: setattr(e, "id", 1)
        # Patch Event constructor to return our mock instance
        with patch("database.event.Event", return_value=mock_event_instance):
            result, status = create_event(data)
            assert status == 201
            assert result["id"] == 1
            assert result["name"] == "New Event"

def test_create_event_missing_fields():
    data = {"name": "No Location"}
    result, status = create_event(data)
    assert status == 400
    assert "Missing required fields" in result["error"]

def test_create_event_invalid_datetime():
    data = {
        "name": "Bad Event",
        "start_time": "invalid-date",
        "end_time": "2025-12-01T12:00:00",
        "location": "Somewhere",
    }
    result, status = create_event(data)
    assert status == 400
    assert "'start_time' must be a valid ISO datetime string" in result["error"]

def test_create_event_end_before_start():
    data = {
        "name": "Backwards Event",
        "start_time": "2025-12-01T12:00:00",
        "end_time": "2025-12-01T10:00:00",
        "location": "Somewhere",
    }
    result, status = create_event(data)
    assert status == 400
    assert "'end_time' must be after 'start_time'" in result["error"]


# Test delete_event

def test_delete_event_success():
    mock_event_instance = MagicMock(spec=Event)

    with patch("database.event.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.get.return_value = mock_event_instance
        mock_session.delete.return_value = None
        mock_session.commit.return_value = None

        result, status = delete_event(1)
        assert status == 200
        assert "deleted" in result["message"]

def test_delete_event_not_found():
    with patch("database.event.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.get.return_value = None

        result, status = delete_event(999)
        assert status == 404
        assert "not found" in result["error"]

def test_delete_event_invalid_id():
    result, status = delete_event("abc")
    assert status == 400
    assert "must be an integer" in result["error"]