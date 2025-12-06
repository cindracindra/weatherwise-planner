"""
Test cases for web routes.

These tests verify that the Flask web routes properly handle requests,
render templates, and interact with database functions correctly.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from app import create_app
from utils.response import build_response, StatusCode


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_profiles_response():
    """Mock profiles response."""
    return build_response(StatusCode.OK, {
        "profiles": [
            {"id": 1, "name": "Test Profile 1"},
            {"id": 2, "name": "Test Profile 2"}
        ]
    })


@pytest.fixture
def mock_events_response():
    """Mock events response."""
    return build_response(StatusCode.OK, {
        "events": [
            {
                "id": 1,
                "name": "Test Event",
                "start_time": "2025-12-10T10:00:00",
                "end_time": "2025-12-10T12:00:00",
                "location": "Test Location"
            }
        ]
    })


# ========== Homepage Tests ==========

class TestHomepage:
    """Test cases for homepage route."""

    def test_homepage_no_profile(self, client, mock_profiles_response):
        """Test homepage renders without selected profile."""
        with patch('routes.web_routes.get_profiles', return_value=mock_profiles_response):
            with patch('routes.web_routes.get_today_detail', return_value={"year": 2025, "month": 12, "day": 6}):
                with patch('routes.web_routes.get_full_calendar', return_value=[]):
                    with patch('routes.web_routes.get_hourly_forecast_today', return_value=[]):
                        response = client.get('/')
                        assert response.status_code == 200
                        assert b'Test Profile 1' in response.data

    def test_homepage_with_profile(self, client, mock_profiles_response, mock_events_response):
        """Test homepage renders with selected profile."""
        with patch('routes.web_routes.get_profiles', return_value=mock_profiles_response):
            with patch('routes.web_routes.get_today_detail', return_value={"year": 2025, "month": 12, "day": 6}):
                with patch('routes.web_routes.get_full_calendar', return_value=[]):
                    with patch('routes.web_routes.get_hourly_forecast_today', return_value=[]):
                        with patch('routes.web_routes.get_events_by_profileid_by_month', return_value=mock_events_response):
                            with patch('routes.web_routes.build_daily_event_list', return_value=[]):
                                response = client.get('/?profileid=1')
                                assert response.status_code == 200

    def test_homepage_with_error_flash(self, client, mock_profiles_response):
        """Test homepage displays error flash message."""
        with patch('routes.web_routes.get_profiles', return_value=mock_profiles_response):
            with patch('routes.web_routes.get_today_detail', return_value={"year": 2025, "month": 12, "day": 6}):
                with patch('routes.web_routes.get_full_calendar', return_value=[]):
                    with patch('routes.web_routes.get_hourly_forecast_today', return_value=[]):
                        response = client.get('/?isReqSucc=False')
                        assert response.status_code == 200


# ========== Management Routes Tests ==========

class TestManagementRoutes:
    """Test cases for management routes."""

    def test_reload_calendar(self, client):
        """Test calendar reload redirects correctly."""
        response = client.get('/reload?profileid=1')
        assert response.status_code == 302
        assert '/?' in response.location

    def test_management_handle_form_no_profile(self, client):
        """Test management form handler without profile."""
        response = client.get('/management')
        assert response.status_code == 302
        assert 'isReqSucc=False' in response.location

    def test_management_handle_form_with_profile(self, client):
        """Test management form handler with profile."""
        response = client.get('/management?profileid=1')
        assert response.status_code == 302
        assert 'profileid=1' in response.location

    def test_web_management_page(self, client, mock_events_response):
        """Test event management page renders."""
        with patch('routes.web_routes.get_events_by_profileid', return_value=mock_events_response):
            with patch('routes.web_routes.group_all_events_by_full_date', return_value=[]):
                response = client.get('/management/event?profileid=1')
                assert response.status_code == 200

    def test_web_management_with_selected_event(self, client, mock_events_response):
        """Test event management page with selected event."""
        event_response = build_response(StatusCode.OK, {
            "id": 1,
            "name": "Test Event",
            "start_time": "2025-12-10T10:00:00",
            "end_time": "2025-12-10T12:00:00",
            "location": "Test Location"
        })
        
        with patch('routes.web_routes.get_events_by_profileid', return_value=mock_events_response):
            with patch('routes.web_routes.get_event_by_id', return_value=event_response):
                with patch('routes.web_routes.group_all_events_by_full_date', return_value=[]):
                    with patch('routes.web_routes.parse_event_for_datepicker', return_value={}):
                        response = client.get('/management/event?profileid=1&selected_eventid=1')
                        assert response.status_code == 200


# ========== Event CRUD Web Routes Tests ==========

class TestEventCRUDWebRoutes:
    """Test cases for event CRUD web routes."""

    def test_web_load_event(self, client):
        """Test loading event for editing."""
        response = client.post('/management/event/load', data={
            'profileid': '1',
            'eventid': '1'
        })
        assert response.status_code == 302
        assert 'selected_eventid=1' in response.location

    def test_web_create_event(self, client):
        """Test creating event from web form."""
        mock_response = build_response(StatusCode.CREATED, {
            "event": {"id": 1},
            "eventxprofile": {"id": 1}
        })
        
        with patch('routes.web_routes.create_event_and_profile_association', return_value=mock_response):
            response = client.post('/management/event/create', data={
                'profileid': '1',
                'name': 'New Event',
                'start_time': '2025-12-10T10:00',
                'end_time': '12:00',
                'location': 'Test Location'
            })
            assert response.status_code == 302
            assert 'reqHttpCode=201' in response.location

    def test_web_update_event(self, client):
        """Test updating event from web form."""
        mock_response = build_response(StatusCode.OK, {
            "id": 1,
            "name": "Updated Event"
        })
        
        with patch('routes.web_routes.update_event', return_value=mock_response):
            response = client.post('/management/event/update', data={
                'profileid': '1',
                'eventid': '1',
                'name': 'Updated Event',
                'start_time': '2025-12-10T10:00',
                'end_time': '12:00',
                'location': 'Test Location'
            })
            assert response.status_code == 302
            assert 'reqHttpCode=200' in response.location

    def test_web_delete_event(self, client):
        """Test deleting event from web form."""
        mock_response = build_response(StatusCode.OK, {
            "deleted_event": {"id": 1},
            "deleted_eventxprofiles": [],
            "count": 0
        })
        
        with patch('routes.web_routes.delete_event_and_profile_association', return_value=mock_response):
            response = client.post('/management/event/delete', data={
                'profileid': '1',
                'eventid': '1'
            })
            assert response.status_code == 302
            assert 'reqHttpCode=200' in response.location


# ========== Profile Management Web Routes Tests ==========

class TestProfileManagementWebRoutes:
    """Test cases for profile management web routes."""

    def test_web_profile_page(self, client, mock_profiles_response):
        """Test profile management page renders."""
        with patch('routes.web_routes.get_profiles', return_value=mock_profiles_response):
            response = client.get('/management/profile')
            assert response.status_code == 200
            assert b'Test Profile 1' in response.data

    def test_web_profile_page_with_success(self, client, mock_profiles_response):
        """Test profile page with success flash message."""
        with patch('routes.web_routes.get_profiles', return_value=mock_profiles_response):
            response = client.get('/management/profile?reqHttpCode=201')
            assert response.status_code == 200

    def test_web_profile_page_with_error(self, client, mock_profiles_response):
        """Test profile page with error flash message."""
        with patch('routes.web_routes.get_profiles', return_value=mock_profiles_response):
            response = client.get('/management/profile?reqHttpCode=400')
            assert response.status_code == 200

    def test_web_create_profile(self, client):
        """Test creating profile from web form."""
        mock_response = build_response(StatusCode.CREATED, {
            "id": 1,
            "name": "New Profile"
        })
        
        with patch('routes.web_routes.create_profile', return_value=mock_response):
            response = client.post('/management/profile/create', data={
                'name': 'New Profile'
            })
            assert response.status_code == 302
            assert 'reqHttpCode=201' in response.location

    def test_web_delete_profile(self, client):
        """Test deleting profile from web form."""
        mock_response = build_response(StatusCode.OK, {
            "message": "Profile 1 deleted."
        })
        
        with patch('routes.web_routes.delete_profile', return_value=mock_response):
            response = client.post('/management/profile/delete', data={
                'profileid': '1'
            })
            assert response.status_code == 302
            assert 'reqHttpCode=200' in response.location
