"""
Test cases for API routes.

These tests verify that the Flask API routes properly handle requests
and return the correct standardized responses for all CRUD operations.
"""

import pytest
from unittest.mock import patch
from flask import jsonify
from app import create_app
from utils.response import StatusCode, build_response


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ========== Event API Tests ==========

class TestEventAPI:
    """Test cases for Event API endpoints."""

    def test_get_events_success(self, client):
        """Test GET /api/events returns all events."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "events": [
                    {
                        "id": 1,
                        "name": "Test Event 1",
                        "start_time": "2025-12-01T10:00:00",
                        "end_time": "2025-12-01T12:00:00",
                        "location": "Location 1"
                    }
                ]
            })
            
            with patch('routes.api_routes.get_events', return_value=mock_response):
                response = client.get('/api/events')
                assert response.status_code == 200
                data = response.get_json()
                assert data["statusCode"] == 200
                assert data["statusMessage"] == "SUCCESS"
                assert "events" in data["data"]
                assert len(data["data"]["events"]) == 1

    def test_get_event_by_id_success(self, client):
        """Test GET /api/events/<id> returns specific event."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "id": 1,
                "name": "Test Event",
                "start_time": "2025-12-01T10:00:00",
                "end_time": "2025-12-01T12:00:00",
                "location": "Test Location"
            })
            
            with patch('routes.api_routes.get_event_by_id', return_value=mock_response):
                response = client.get('/api/events/1')
                assert response.status_code == 200
                data = response.get_json()
                assert data["statusCode"] == 200
                assert data["data"]["id"] == 1

    def test_get_event_by_id_not_found(self, client):
        """Test GET /api/events/<id> returns 404 when event doesn't exist."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.NOT_FOUND, {
                "error": "Event with id 999 not found."
            })
            
            with patch('routes.api_routes.get_event_by_id', return_value=mock_response):
                response = client.get('/api/events/999')
                assert response.status_code == 404
                data = response.get_json()
                assert data["statusCode"] == 404
                assert "error" in data["data"]

    def test_create_event_success(self, client):
        """Test POST /api/events creates new event."""
        event_data = {
            "name": "New Event",
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T12:00:00",
            "location": "New Location"
        }
        
        with client.application.app_context():
            mock_response = build_response(StatusCode.CREATED, {
                "id": 1,
                **event_data
            })
            
            with patch('routes.api_routes.create_event', return_value=mock_response):
                response = client.post('/api/events', json=event_data)
                assert response.status_code == 201
                data = response.get_json()
                assert data["statusCode"] == 201
                assert data["statusMessage"] == "CREATED"

    def test_update_event_success(self, client):
        """Test PATCH /api/events/<id> updates event."""
        update_data = {"name": "Updated Event", "location": "Updated Location"}
        
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "id": 1,
                "name": "Updated Event",
                "start_time": "2025-12-01T10:00:00",
                "end_time": "2025-12-01T12:00:00",
                "location": "Updated Location"
            })
            
            with patch('routes.api_routes.update_event', return_value=mock_response):
                response = client.patch('/api/events/1', json=update_data)
                assert response.status_code == 200
                data = response.get_json()
                assert data["statusCode"] == 200
                assert data["data"]["name"] == "Updated Event"

    def test_delete_event_success(self, client):
        """Test DELETE /api/events/<id> deletes event."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "message": "Event 1 deleted."
            })
            
            with patch('routes.api_routes.delete_event', return_value=mock_response):
                response = client.delete('/api/events/1')
                assert response.status_code == 200
                data = response.get_json()
                assert data["statusCode"] == 200
                assert "deleted" in data["data"]["message"]


# ========== Profile API Tests ==========

class TestProfileAPI:
    """Test cases for Profile API endpoints."""

    def test_get_profiles_success(self, client):
        """Test GET /api/profiles returns all profiles."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "profiles": [
                    {"id": 1, "name": "Profile 1"},
                    {"id": 2, "name": "Profile 2"}
                ]
            })
            
            with patch('routes.api_routes.get_profiles', return_value=mock_response):
                response = client.get('/api/profiles')
                assert response.status_code == 200
                data = response.get_json()
                assert data["statusCode"] == 200
                assert len(data["data"]["profiles"]) == 2

    def test_get_profile_by_id_success(self, client):
        """Test GET /api/profiles/<id> returns specific profile."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "id": 1,
                "name": "Test Profile"
            })
            
            with patch('routes.api_routes.get_profile_by_id', return_value=mock_response):
                response = client.get('/api/profiles/1')
                assert response.status_code == 200
                data = response.get_json()
                assert data["data"]["name"] == "Test Profile"

    def test_create_profile_success(self, client):
        """Test POST /api/profiles creates new profile."""
        profile_data = {"profile_name": "New Profile"}
        
        with client.application.app_context():
            mock_response = build_response(StatusCode.CREATED, {
                "id": 1,
                "name": "New Profile"
            })
            
            with patch('routes.api_routes.create_profile', return_value=mock_response):
                response = client.post('/api/profiles', json=profile_data)
                assert response.status_code == 201
                data = response.get_json()
                assert data["statusCode"] == 201

    def test_delete_profile_success(self, client):
        """Test DELETE /api/profiles/<id> deletes profile."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "message": "Profile 1 deleted."
            })
            
            with patch('routes.api_routes.delete_profile', return_value=mock_response):
                response = client.delete('/api/profiles/1')
                assert response.status_code == 200
                data = response.get_json()
                assert data["statusCode"] == 200


# ========== Event-Profile Association API Tests ==========

class TestEventProfileAPI:
    """Test cases for Event-Profile association API endpoints."""

    def test_get_event_profiles_success(self, client):
        """Test GET /api/event-profiles returns all associations."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "event_profiles": [
                    {"event_id": 1, "profile_id": 1},
                    {"event_id": 2, "profile_id": 1}
                ]
            })
            
            with patch('routes.api_routes.get_eventxprofiles', return_value=mock_response):
                response = client.get('/api/event-profiles')
                assert response.status_code == 200
                data = response.get_json()
                assert len(data["data"]["event_profiles"]) == 2

    def test_get_event_profile_by_id_success(self, client):
        """Test GET /api/event-profiles/<id> returns specific association."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "id": 1,
                "event_id": 1,
                "profile_id": 1
            })
            
            with patch('routes.api_routes.get_eventxprofile_by_id', return_value=mock_response):
                response = client.get('/api/event-profiles/1')
                assert response.status_code == 200
                data = response.get_json()
                assert data["data"]["event_id"] == 1

    def test_create_event_profile_success(self, client):
        """Test POST /api/event-profiles creates new association."""
        association_data = {"eventid": 1, "profileid": 1}
        
        with client.application.app_context():
            mock_response = build_response(StatusCode.CREATED, {
                "id": 1,
                "event_id": 1,
                "profile_id": 1
            })
            
            with patch('routes.api_routes.create_eventxprofile', return_value=mock_response):
                response = client.post('/api/event-profiles', json=association_data)
                assert response.status_code == 201
                data = response.get_json()
                assert data["statusCode"] == 201

    def test_delete_event_profile_success(self, client):
        """Test DELETE /api/event-profiles/<id> deletes association."""
        with client.application.app_context():
            mock_response = build_response(StatusCode.OK, {
                "message": "EventXProfile 1 deleted."
            })
            
            with patch('routes.api_routes.delete_eventxprofile', return_value=mock_response):
                response = client.delete('/api/event-profiles/1')
                assert response.status_code == 200
                data = response.get_json()
                assert data["statusCode"] == 200

#                 data = response.get_json()
#                 assert "error" in data
#                 assert "not found" in data["error"].lower()

#     def test_get_event_by_id_invalid_id(self, client):
#         """Test GET /api/events/<id> with invalid ID type."""
#         mock_error = (
#             {"error": "Field 'event_id' must be an integer."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.get_event_by_id', return_value=mock_error):
#             response = client.get('/api/events/abc')
#             # Flask will return 404 for invalid int in route
#             assert response.status_code == 404

#     def test_create_event_success(self, client):
#         """Test POST /api/events creates a new event."""
#         event_data = {
#             "name": "New Event",
#             "start_time": "2025-12-05T10:00:00",
#             "end_time": "2025-12-05T12:00:00",
#             "location": "New Location"
#         }

#         mock_response = (
#             {
#                 "id": 1,
#                 "name": "New Event",
#                 "start_time": "2025-12-05T10:00:00",
#                 "end_time": "2025-12-05T12:00:00",
#                 "location": "New Location"
#             },
#             StatusCode.CREATED.value
#         )

#         with patch('routes.api_routes.create_event', return_value=mock_response):
#             response = client.post('/api/events', json=event_data)
#             assert response.status_code == 201
#             data = response.get_json()
#             assert data["id"] == 1
#             assert data["name"] == "New Event"

#     def test_create_event_missing_fields(self, client):
#         """Test POST /api/events with missing required fields."""
#         event_data = {
#             "name": "Incomplete Event"
#             # Missing start_time, end_time, location
#         }

#         mock_error = (
#             {"error": "Missing required fields: 'start_time', 'end_time', 'location'."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.create_event', return_value=mock_error):
#             response = client.post('/api/events', json=event_data)
#             assert response.status_code == 400
#             data = response.get_json()
#             assert "error" in data
#             assert "Missing required fields" in data["error"]

#     def test_create_event_invalid_datetime(self, client):
#         """Test POST /api/events with invalid datetime format."""
#         event_data = {
#             "name": "Bad Event",
#             "start_time": "not-a-date",
#             "end_time": "2025-12-05T12:00:00",
#             "location": "Location"
#         }

#         mock_error = (
#             {"error": "Field 'start_time' must be a valid ISO datetime string."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.create_event', return_value=mock_error):
#             response = client.post('/api/events', json=event_data)
#             assert response.status_code == 400
#             data = response.get_json()
#             assert "error" in data
#             assert "datetime" in data["error"].lower()

#     def test_create_event_end_before_start(self, client):
#         """Test POST /api/events with end_time before start_time."""
#         event_data = {
#             "name": "Backwards Event",
#             "start_time": "2025-12-05T12:00:00",
#             "end_time": "2025-12-05T10:00:00",
#             "location": "Location"
#         }

#         mock_error = (
#             {"error": "Field 'end_time' must be after 'start_time'."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.create_event', return_value=mock_error):
#             response = client.post('/api/events', json=event_data)
#             assert response.status_code == 400
#             data = response.get_json()
#             assert "error" in data
#             assert "after" in data["error"].lower()

#     def test_update_event_success(self, client):
#         """Test PATCH /api/events/<id> updates an event."""
#         update_data = {
#             "name": "Updated Event"
#         }

#         mock_response = (
#             {
#                 "id": 1,
#                 "name": "Updated Event",
#                 "start_time": "2025-12-01T10:00:00",
#                 "end_time": "2025-12-01T12:00:00",
#                 "location": "Original Location"
#             },
#             StatusCode.OK.value
#         )

#         with patch('routes.api_routes.update_event', return_value=mock_response):
#             response = client.patch('/api/events/1', json=update_data)
#             assert response.status_code == 200
#             data = response.get_json()
#             assert data["name"] == "Updated Event"

#     def test_update_event_not_found(self, client):
#         """Test PATCH /api/events/<id> with non-existent event."""
#         update_data = {"name": "Updated Event"}

#         mock_error = (
#             {"error": "Event with id 999 not found."},
#             StatusCode.NOT_FOUND.value
#         )

#         with patch('routes.api_routes.update_event', return_value=mock_error):
#             response = client.patch('/api/events/999', json=update_data)
#             assert response.status_code == 404
#             data = response.get_json()
#             assert "error" in data
#             assert "not found" in data["error"].lower()

#     def test_update_event_invalid_datetime(self, client):
#         """Test PATCH /api/events/<id> with invalid datetime."""
#         update_data = {
#             "start_time": "invalid-date"
#         }

#         mock_error = (
#             {"error": "Field 'start_time' must be a valid ISO datetime string."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.update_event', return_value=mock_error):
#             response = client.patch('/api/events/1', json=update_data)
#             assert response.status_code == 400
#             data = response.get_json()
#             assert "error" in data

#     def test_delete_event_success(self, client):
#         """Test DELETE /api/events/<id> deletes an event."""
#         mock_response = (
#             {"message": "Event 1 deleted."},
#             StatusCode.OK.value
#         )

#         with patch('routes.api_routes.delete_event', return_value=mock_response):
#             response = client.delete('/api/events/1')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert "message" in data
#             assert "deleted" in data["message"].lower()

#     def test_delete_event_not_found(self, client):
#         """Test DELETE /api/events/<id> with non-existent event."""
#         mock_error = (
#             {"error": "Event with id 999 not found."},
#             StatusCode.NOT_FOUND.value
#         )

#         with patch('routes.api_routes.delete_event', return_value=mock_error):
#             response = client.delete('/api/events/999')
#             assert response.status_code == 404
#             data = response.get_json()
#             assert "error" in data
#             assert "not found" in data["error"].lower()


# # ========== Profile API Tests ==========

# class TestProfileAPI:
#     """Test cases for Profile API endpoints."""

#     def test_get_profiles_success(self, client):
#         """Test GET /api/profiles returns all profiles."""
#         mock_profiles = {
#             "profiles": [
#                 {"id": 1, "name": "Profile 1"},
#                 {"id": 2, "name": "Profile 2"}
#             ]
#         }

#         with patch('routes.api_routes.get_profiles', return_value=mock_profiles):
#             response = client.get('/api/profiles')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert "profiles" in data
#             assert len(data["profiles"]) == 2

#     def test_get_profiles_empty(self, client):
#         """Test GET /api/profiles returns empty list when no profiles exist."""
#         mock_profiles = {"profiles": []}

#         with patch('routes.api_routes.get_profiles', return_value=mock_profiles):
#             response = client.get('/api/profiles')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert "profiles" in data
#             assert len(data["profiles"]) == 0

#     def test_get_profile_by_id_success(self, client):
#         """Test GET /api/profiles/<id> returns specific profile."""
#         mock_profile = (
#             {"id": 1, "name": "Test Profile"},
#             StatusCode.OK.value
#         )

#         with patch('routes.api_routes.get_profile_by_id', return_value=mock_profile):
#             response = client.get('/api/profiles/1')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert data["id"] == 1
#             assert data["name"] == "Test Profile"

#     def test_get_profile_by_id_not_found(self, client):
#         """Test GET /api/profiles/<id> returns 404 when profile doesn't exist."""
#         mock_error = (
#             {"error": "Profile with id 999 not found."},
#             StatusCode.NOT_FOUND.value
#         )

#         with patch('routes.api_routes.get_profile_by_id', return_value=mock_error):
#             response = client.get('/api/profiles/999')
#             assert response.status_code == 404
#             data = response.get_json()
#             assert "error" in data
#             assert "not found" in data["error"].lower()

#     def test_create_profile_success(self, client):
#         """Test POST /api/profiles creates a new profile."""
#         profile_data = {"name": "New Profile"}

#         mock_response = (
#             {"id": 1, "name": "New Profile"},
#             StatusCode.CREATED.value
#         )

#         with patch('routes.api_routes.create_profile', return_value=mock_response):
#             response = client.post('/api/profiles', json=profile_data)
#             assert response.status_code == 201
#             data = response.get_json()
#             assert data["id"] == 1
#             assert data["name"] == "New Profile"

#     def test_create_profile_missing_name(self, client):
#         """Test POST /api/profiles with missing name field."""
#         profile_data = {}

#         mock_error = (
#             {"error": "Missing required fields: 'name'."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.create_profile', return_value=mock_error):
#             response = client.post('/api/profiles', json=profile_data)
#             assert response.status_code == 400
#             data = response.get_json()
#             assert "error" in data
#             assert "Missing required fields" in data["error"]

#     def test_create_profile_empty_name(self, client):
#         """Test POST /api/profiles with empty name."""
#         profile_data = {"name": ""}

#         mock_error = (
#             {"error": "Missing required fields: 'name'."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.create_profile', return_value=mock_error):
#             response = client.post('/api/profiles', json=profile_data)
#             assert response.status_code == 400
#             data = response.get_json()
#             assert "error" in data

#     def test_delete_profile_success(self, client):
#         """Test DELETE /api/profiles/<id> deletes a profile."""
#         mock_response = (
#             {"message": "Profile 1 deleted."},
#             StatusCode.OK.value
#         )

#         with patch('routes.api_routes.delete_profile', return_value=mock_response):
#             response = client.delete('/api/profiles/1')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert "message" in data
#             assert "deleted" in data["message"].lower()

#     def test_delete_profile_not_found(self, client):
#         """Test DELETE /api/profiles/<id> with non-existent profile."""
#         mock_error = (
#             {"error": "Profile with id 999 not found."},
#             StatusCode.NOT_FOUND.value
#         )

#         with patch('routes.api_routes.delete_profile', return_value=mock_error):
#             response = client.delete('/api/profiles/999')
#             assert response.status_code == 404
#             data = response.get_json()
#             assert "error" in data
#             assert "not found" in data["error"].lower()


# # ========== Event-Profile API Tests ==========

# class TestEventProfileAPI:
#     """Test cases for Event-Profile association API endpoints."""

#     def test_get_event_profiles_success(self, client):
#         """Test GET /api/event-profiles returns all associations."""
#         mock_associations = {
#             "event_profiles": [
#                 {"event_id": 1, "profile_id": 1},
#                 {"event_id": 2, "profile_id": 1},
#                 {"event_id": 1, "profile_id": 2}
#             ]
#         }

#         with patch('routes.api_routes.get_eventxprofiles', return_value=mock_associations):
#             response = client.get('/api/event-profiles')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert "event_profiles" in data
#             assert len(data["event_profiles"]) == 3

#     def test_get_event_profiles_empty(self, client):
#         """Test GET /api/event-profiles returns empty list when no associations exist."""
#         mock_associations = {"event_profiles": []}

#         with patch('routes.api_routes.get_eventxprofiles', return_value=mock_associations):
#             response = client.get('/api/event-profiles')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert "event_profiles" in data
#             assert len(data["event_profiles"]) == 0

#     def test_get_event_profile_by_id_success(self, client):
#         """Test GET /api/event-profiles/<id> returns specific association."""
#         mock_association = (
#             {"id": 1, "event_id": 1, "profile_id": 1},
#             StatusCode.OK.value
#         )

#         with patch('routes.api_routes.get_eventxprofile_by_id', return_value=mock_association):
#             response = client.get('/api/event-profiles/1')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert data["id"] == 1
#             assert data["event_id"] == 1
#             assert data["profile_id"] == 1

#     def test_get_event_profile_by_id_not_found(self, client):
#         """Test GET /api/event-profiles/<id> returns 404 when association doesn't exist."""
#         mock_error = (
#             {"error": "EventXProfile with id 999 not found."},
#             StatusCode.NOT_FOUND.value
#         )

#         with patch('routes.api_routes.get_eventxprofile_by_id', return_value=mock_error):
#             response = client.get('/api/event-profiles/999')
#             assert response.status_code == 404
#             data = response.get_json()
#             assert "error" in data
#             assert "not found" in data["error"].lower()

#     def test_create_event_profile_success(self, client):
#         """Test POST /api/event-profiles creates a new association."""
#         association_data = {
#             "eventid": 1,
#             "profileid": 1
#         }

#         mock_response = (
#             {"id": 1, "event_id": 1, "profile_id": 1},
#             StatusCode.CREATED.value
#         )

#         with patch('routes.api_routes.create_eventxprofile', return_value=mock_response):
#             response = client.post('/api/event-profiles', json=association_data)
#             assert response.status_code == 201
#             data = response.get_json()
#             assert data["id"] == 1
#             assert data["event_id"] == 1
#             assert data["profile_id"] == 1

#     def test_create_event_profile_missing_fields(self, client):
#         """Test POST /api/event-profiles with missing required fields."""
#         association_data = {"eventid": 1}  # Missing profileid

#         mock_error = (
#             {"error": "Missing required fields: 'profileid'."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.create_eventxprofile', return_value=mock_error):
#             response = client.post('/api/event-profiles', json=association_data)
#             assert response.status_code == 400
#             data = response.get_json()
#             assert "error" in data
#             assert "Missing required fields" in data["error"]

#     def test_create_event_profile_invalid_ids(self, client):
#         """Test POST /api/event-profiles with invalid ID types."""
#         association_data = {
#             "eventid": "not-a-number",
#             "profileid": 1
#         }

#         mock_error = (
#             {"error": "Fields 'eventid' and 'profileid' must be integers."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.create_eventxprofile', return_value=mock_error):
#             response = client.post('/api/event-profiles', json=association_data)
#             assert response.status_code == 400
#             data = response.get_json()
#             assert "error" in data
#             assert "must be integers" in data["error"]

#     def test_create_event_profile_not_found(self, client):
#         """Test POST /api/event-profiles when event or profile doesn't exist."""
#         association_data = {
#             "eventid": 999,
#             "profileid": 999
#         }

#         mock_error = (
#             {"error": "Event or Profile not found."},
#             StatusCode.NOT_FOUND.value
#         )

#         with patch('routes.api_routes.create_eventxprofile', return_value=mock_error):
#             response = client.post('/api/event-profiles', json=association_data)
#             assert response.status_code == 404
#             data = response.get_json()
#             assert "error" in data
#             assert "not found" in data["error"].lower()

#     def test_delete_event_profile_success(self, client):
#         """Test DELETE /api/event-profiles/<id> deletes an association."""
#         mock_response = (
#             {"message": "EventXProfile 1 deleted."},
#             StatusCode.OK.value
#         )

#         with patch('routes.api_routes.delete_eventxprofile', return_value=mock_response):
#             response = client.delete('/api/event-profiles/1')
#             assert response.status_code == 200
#             data = response.get_json()
#             assert "message" in data
#             assert "deleted" in data["message"].lower()

#     def test_delete_event_profile_not_found(self, client):
#         """Test DELETE /api/event-profiles/<id> with non-existent association."""
#         mock_error = (
#             {"error": "EventXProfile with id 999 not found."},
#             StatusCode.NOT_FOUND.value
#         )

#         with patch('routes.api_routes.delete_eventxprofile', return_value=mock_error):
#             response = client.delete('/api/event-profiles/999')
#             assert response.status_code == 404
#             data = response.get_json()
#             assert "error" in data
#             assert "not found" in data["error"].lower()

#     def test_delete_event_profile_invalid_id(self, client):
#         """Test DELETE /api/event-profiles/<id> with invalid ID type."""
#         mock_error = (
#             {"error": "Field 'event_profile_id' must be an integer."},
#             StatusCode.BAD_REQUEST.value
#         )

#         with patch('routes.api_routes.delete_eventxprofile', return_value=mock_error):
#             response = client.delete('/api/event-profiles/abc')
#             # Flask will return 404 for invalid int in route
#             assert response.status_code == 404


# # ========== Error Handling Tests ==========

# class TestAPIErrorHandling:
#     """Test cases for API error handling."""

#     def test_event_endpoint_no_json_body(self, client):
#         """Test POST /api/events without JSON body."""
#         response = client.post('/api/events')
#         # Flask returns 415 Unsupported Media Type when no JSON body is provided
#         assert response.status_code in [400, 415, 500]

#     def test_profile_endpoint_no_json_body(self, client):
#         """Test POST /api/profiles without JSON body."""
#         response = client.post('/api/profiles')
#         # Flask returns 415 Unsupported Media Type when no JSON body is provided
#         assert response.status_code in [400, 415, 500]

#     def test_event_profile_endpoint_no_json_body(self, client):
#         """Test POST /api/event-profiles without JSON body."""
#         response = client.post('/api/event-profiles')
#         # Flask returns 415 Unsupported Media Type when no JSON body is provided
#         assert response.status_code in [400, 415, 500]

#     def test_invalid_json_format(self, client):
#         """Test POST with invalid JSON format."""
#         response = client.post(
#             '/api/events',
#             data='not-valid-json',
#             content_type='application/json'
#         )
#         assert response.status_code in [400, 500]

#     def test_nonexistent_endpoint(self, client):
#         """Test accessing non-existent API endpoint."""
#         response = client.get('/api/nonexistent')
#         assert response.status_code == 404

#     def test_method_not_allowed(self, client):
#         """Test using wrong HTTP method on endpoint."""
#         # Try PUT on events endpoint (not supported)
#         response = client.put('/api/events/1')
#         assert response.status_code == 405  # Method Not Allowed
