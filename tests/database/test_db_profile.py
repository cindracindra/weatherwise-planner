import pytest
from unittest.mock import patch, MagicMock
from database.db_profile import get_profiles, create_profile, delete_profile
from models.db_models.profile import Profile
from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


# Test get_profiles

def test_get_profiles(app):
    with app.app_context():
        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.name = "Test Profile"

        with patch("database.db_profile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = [mock_profile]

            response, status = get_profiles()
            result = response.get_json()
            assert result["statusCode"] == 200
            assert result["statusMessage"] == "SUCCESS"
            assert "profiles" in result["data"]
            assert len(result["data"]["profiles"]) == 1
            assert result["data"]["profiles"][0]["name"] == "Test Profile"


# Test create_profile

def test_create_profile_success(app):
    with app.app_context():
        data = {"profile_name": "New Profile"}

        mock_profile_instance = MagicMock(spec=Profile)
        mock_profile_instance.id = 1
        mock_profile_instance.name = "New Profile"

        with patch("database.db_profile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.side_effect = lambda e: setattr(e, "id", 1)
            with patch("database.db_profile.Profile", return_value=mock_profile_instance):
                response, status = create_profile(data)
                result = response.get_json()
                assert status == 201
                assert result["statusCode"] == 201
                assert result["statusMessage"] == "CREATED"
                assert result["data"]["id"] == 1
                assert result["data"]["name"] == "New Profile"

def test_create_profile_missing_name(app):
    with app.app_context():
        data = {}
        response, status = create_profile(data)
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "Missing required fields" in result["data"]["error"]


# Test delete_profile

def test_delete_profile_success(app):
    with app.app_context():
        mock_profile_instance = MagicMock(spec=Profile)

        with patch("database.db_profile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = mock_profile_instance
            mock_session.delete.return_value = None
            mock_session.commit.return_value = None

            response, status = delete_profile(1)
            result = response.get_json()
            assert status == 200
            assert result["statusCode"] == 200
            assert result["statusMessage"] == "SUCCESS"
            assert "deleted" in result["data"]["message"]

def test_delete_profile_not_found(app):
    with app.app_context():
        with patch("database.db_profile.Session") as mock_session_class:
            mock_session = mock_session_class.return_value.__enter__.return_value
            mock_session.get.return_value = None

            response, status = delete_profile(999)
            result = response.get_json()
            assert status == 404
            assert result["statusCode"] == 404
            assert result["statusMessage"] == "NOT_FOUND"
            assert "not found" in result["data"]["error"]

def test_delete_profile_invalid_id(app):
    with app.app_context():
        response, status = delete_profile("abc")
        result = response.get_json()
        assert status == 400
        assert result["statusCode"] == 400
        assert result["statusMessage"] == "BAD_REQUEST"
        assert "must be an integer" in result["data"]["error"]