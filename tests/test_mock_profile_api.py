import pytest
from unittest.mock import patch, MagicMock
from database.profile import get_profiles, create_profile, delete_profile
from models.db_models.profile import Profile


# Test get_profiles

def test_get_profiles():
    mock_profile = MagicMock(spec=Profile)
    mock_profile.id = 1
    mock_profile.name = "Test Profile"

    with patch("database.profile.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = [mock_profile]

        result = get_profiles()
        assert "profiles" in result
        assert len(result["profiles"]) == 1
        assert result["profiles"][0]["name"] == "Test Profile"


# Test create_profile

def test_create_profile_success():
    data = {"profile_name": "New Profile"}

    mock_profile_instance = MagicMock(spec=Profile)
    mock_profile_instance.id = 1
    mock_profile_instance.name = "New Profile"

    with patch("database.profile.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda e: setattr(e, "id", 1)
        with patch("database.profile.Profile", return_value=mock_profile_instance):
            result, status = create_profile(data)
            assert status == 201
            assert result["id"] == 1
            assert result["name"] == "New Profile"

def test_create_profile_missing_name():
    data = {}
    result, status = create_profile(data)
    assert status == 400
    assert "Missing required fields" in result["error"]


# Test delete_profile

def test_delete_profile_success():
    mock_profile_instance = MagicMock(spec=Profile)

    with patch("database.profile.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.get.return_value = mock_profile_instance
        mock_session.delete.return_value = None
        mock_session.commit.return_value = None

        result, status = delete_profile(1)
        assert status == 200
        assert "deleted" in result["message"]

def test_delete_profile_not_found():
    with patch("database.profile.Session") as mock_session_class:
        mock_session = mock_session_class.return_value.__enter__.return_value
        mock_session.get.return_value = None

        result, status = delete_profile(999)
        assert status == 404
        assert "not found" in result["error"]

def test_delete_profile_invalid_id():
    result, status = delete_profile("abc")
    assert status == 400
    assert "must be an integer" in result["error"]