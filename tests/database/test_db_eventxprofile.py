import pytest
from unittest.mock import patch, MagicMock
from database.db_eventxprofile import (
    get_eventxprofiles,
    create_eventxprofile,
    delete_eventxprofile,
)
from models.db_models.event import Event
from models.db_models.profile import Profile
from models.db_models.eventxprofile import EventXProfile
from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


# Test get_event_profiles

def test_get_event_profiles(app):
    with app.app_context():
        mock_ep = MagicMock(spec=EventXProfile)
        mock_ep.eventid = 1
        mock_ep.profileid = 2

        with patch("database.db_eventxprofile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_ep]

            response, status = get_eventxprofiles()
            result = response.get_json()
            assert result["statusCode"] == 200
            assert result["statusMessage"] == "SUCCESS"
            assert "event_profiles" in result["data"]
            assert len(result["data"]["event_profiles"]) == 1
            assert result["data"]["event_profiles"][0]["event_id"] == 1
            assert result["data"]["event_profiles"][0]["profile_id"] == 2


# Test create_event_profile

def test_create_event_profile_success(app):
    with app.app_context():
        data = {"eventid": 1, "profileid": 2}

        mock_event_instance = MagicMock(spec=Event)
        mock_profile_instance = MagicMock(spec=Profile)
        mock_ep_instance = MagicMock(spec=EventXProfile)
        mock_ep_instance.id = 10
        mock_ep_instance.eventid = data["eventid"]
        mock_ep_instance.profileid = data["profileid"]

        with patch("database.db_eventxprofile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            # Mock get for Event and Profile
            mock_session.get.side_effect = lambda cls, id: mock_event_instance if cls == Event else mock_profile_instance
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.side_effect = lambda e: setattr(e, "id", 10)
            # Patch EventXProfile constructor
            with patch("database.db_eventxprofile.EventXProfile", return_value=mock_ep_instance):
                response, status = create_eventxprofile(data)
                result = response.get_json()
                assert status == 201
                assert result["statusCode"] == 201
                assert result["statusMessage"] == "CREATED"
                assert result["data"]["id"] == 10
                assert result["data"]["event_id"] == 1
                assert result["data"]["profile_id"] == 2

def test_create_event_profile_missing_fields(app):
    with app.app_context():
        data = {"eventid": 1}  # missing profileid
        response, status = create_eventxprofile(data)
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "Missing required fields" in result["data"]["error"]

def test_create_event_profile_invalid_ids(app):
    with app.app_context():
        data = {"eventid": "abc", "profileid": "xyz"}
        response, status = create_eventxprofile(data)
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "must be integers" in result["data"]["error"]

def test_create_event_profile_not_found(app):
    with app.app_context():
        data = {"eventid": 1, "profileid": 2}

        with patch("database.db_eventxprofile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            # Return None for get to simulate missing Event/Profile
            mock_session.get.return_value = None
            response, status = create_eventxprofile(data)
            result = response.get_json()
            assert status == 404
            assert result["statusCode"] == 404
            assert result["statusMessage"] == "NOT_FOUND"
            assert "not found" in result["data"]["error"]


# Test delete_event_profile

def test_delete_event_profile_success(app):
    with app.app_context():
        mock_ep_instance = MagicMock(spec=EventXProfile)

        with patch("database.db_eventxprofile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = mock_ep_instance
            mock_session.delete.return_value = None
            mock_session.commit.return_value = None

            response, status = delete_eventxprofile(1)
            result = response.get_json()
            assert status == 200
            assert result["statusCode"] == 200
            assert result["statusMessage"] == "SUCCESS"
            assert "deleted" in result["data"]["message"]

def test_delete_event_profile_not_found(app):
    with app.app_context():
        with patch("database.db_eventxprofile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = None

            response, status = delete_eventxprofile(999)
            result = response.get_json()
            assert status == 404
            assert result["statusCode"] == 404
            assert result["statusMessage"] == "NOT_FOUND"
            assert "not found" in result["data"]["error"]

def test_delete_event_profile_invalid_id(app):
    with app.app_context():
        response, status = delete_eventxprofile("abc")
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "must be an integer" in result["data"]["error"]