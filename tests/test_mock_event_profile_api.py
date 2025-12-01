import pytest
from unittest.mock import patch, MagicMock
from api.event_profile_api import (
    get_event_profiles,
    create_event_profile,
    delete_event_profile,
)
from models.event import Event
from models.profile import Profile
from models.event_profile import Event_Profile


# Test get_event_profiles

def test_get_event_profiles():
    mock_ep = MagicMock(spec=Event_Profile)
    mock_ep.eventid = 1
    mock_ep.profileid = 2

    with patch("api.event_profile_api.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_ep]

        result = get_event_profiles()
        assert "event_profiles" in result
        assert len(result["event_profiles"]) == 1
        assert result["event_profiles"][0]["event_id"] == 1
        assert result["event_profiles"][0]["profile_id"] == 2


# Test create_event_profile

def test_create_event_profile_success():
    data = {"eventid": 1, "profileid": 2}

    mock_event_instance = MagicMock(spec=Event)
    mock_profile_instance = MagicMock(spec=Profile)
    mock_ep_instance = MagicMock(spec=Event_Profile)
    mock_ep_instance.id = 10
    mock_ep_instance.eventid = data["eventid"]
    mock_ep_instance.profileid = data["profileid"]

    with patch("api.event_profile_api.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        # Mock get for Event and Profile
        mock_session.get.side_effect = lambda cls, id: mock_event_instance if cls == Event else mock_profile_instance
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda e: setattr(e, "id", 10)
        # Patch Event_Profile constructor
        with patch("api.event_profile_api.Event_Profile", return_value=mock_ep_instance):
            result, status = create_event_profile(data)
            assert status == 201
            assert result["id"] == 10
            assert result["eventid"] == 1
            assert result["profileid"] == 2

def test_create_event_profile_missing_fields():
    data = {"eventid": 1}  # missing profileid
    result, status = create_event_profile(data)
    assert status == 400
    assert "Missing required fields" in result["error"]

def test_create_event_profile_invalid_ids():
    data = {"eventid": "abc", "profileid": "xyz"}
    result, status = create_event_profile(data)
    assert status == 400
    assert "must be integers" in result["error"]

def test_create_event_profile_not_found():
    data = {"eventid": 1, "profileid": 2}

    with patch("api.event_profile_api.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        # Return None for get to simulate missing Event/Profile
        mock_session.get.return_value = None
        result, status = create_event_profile(data)
        assert status == 404
        assert "not found" in result["error"]


# Test delete_event_profile

def test_delete_event_profile_success():
    mock_ep_instance = MagicMock(spec=Event_Profile)

    with patch("api.event_profile_api.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.get.return_value = mock_ep_instance
        mock_session.delete.return_value = None
        mock_session.commit.return_value = None

        result, status = delete_event_profile(1)
        assert status == 200
        assert "deleted" in result["message"]

def test_delete_event_profile_not_found():
    with patch("api.event_profile_api.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.get.return_value = None

        result, status = delete_event_profile(999)
        assert status == 404
        assert "not found" in result["error"]

def test_delete_event_profile_invalid_id():
    result, status = delete_event_profile("abc")
    assert status == 400
    assert "must be an integer" in result["error"]