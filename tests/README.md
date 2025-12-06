# Test Suite Documentation

## Overview

This test suite provides comprehensive coverage for the Event Calendar Flask Application, including database operations, API routes, and utility functions.

**Total Tests: 94**

## Test Files

### 1. `test_api_routes.py` (40 tests)
Tests all Flask API routes to ensure proper HTTP request/response handling.

#### TestEventAPI (14 tests)
- **GET /api/events**
  - `test_get_events_success` - Returns list of all events
  - `test_get_events_empty` - Returns empty list when no events exist

- **GET /api/events/<id>**
  - `test_get_event_by_id_success` - Returns specific event by ID
  - `test_get_event_by_id_not_found` - Returns 404 for non-existent event
  - `test_get_event_by_id_invalid_id` - Handles invalid ID type

- **POST /api/events**
  - `test_create_event_success` - Creates new event successfully
  - `test_create_event_missing_fields` - Validates required fields
  - `test_create_event_invalid_datetime` - Validates datetime format
  - `test_create_event_end_before_start` - Validates end_time > start_time

- **PATCH /api/events/<id>**
  - `test_update_event_success` - Updates event successfully
  - `test_update_event_not_found` - Returns 404 for non-existent event
  - `test_update_event_invalid_datetime` - Validates datetime format

- **DELETE /api/events/<id>**
  - `test_delete_event_success` - Deletes event successfully
  - `test_delete_event_not_found` - Returns 404 for non-existent event

#### TestProfileAPI (9 tests)
- **GET /api/profiles**
  - `test_get_profiles_success` - Returns list of all profiles
  - `test_get_profiles_empty` - Returns empty list when no profiles exist

- **GET /api/profiles/<id>**
  - `test_get_profile_by_id_success` - Returns specific profile by ID
  - `test_get_profile_by_id_not_found` - Returns 404 for non-existent profile

- **POST /api/profiles**
  - `test_create_profile_success` - Creates new profile successfully
  - `test_create_profile_missing_name` - Validates required name field
  - `test_create_profile_empty_name` - Validates non-empty name

- **DELETE /api/profiles/<id>**
  - `test_delete_profile_success` - Deletes profile successfully
  - `test_delete_profile_not_found` - Returns 404 for non-existent profile

#### TestEventProfileAPI (11 tests)
- **GET /api/eventxprofiles**
  - `test_get_eventxprofiles_success` - Returns list of all associations
  - `test_get_eventxprofiles_empty` - Returns empty list when no associations exist

- **GET /api/eventxprofiles/<id>**
  - `test_get_eventxprofile_by_id_success` - Returns specific association by ID
  - `test_get_eventxprofile_by_id_not_found` - Returns 404 for non-existent association

- **POST /api/eventxprofiles**
  - `test_create_eventxprofile_success` - Creates new association successfully
  - `test_create_eventxprofile_missing_fields` - Validates required fields
  - `test_create_eventxprofile_invalid_ids` - Validates integer IDs
  - `test_create_eventxprofile_not_found` - Returns 404 when event or profile doesn't exist

- **DELETE /api/eventxprofiles/<id>**
  - `test_delete_eventxprofile_success` - Deletes association successfully
  - `test_delete_eventxprofile_not_found` - Returns 404 for non-existent association
  - `test_delete_eventxprofile_invalid_id` - Handles invalid ID type

#### TestAPIErrorHandling (6 tests)
- `test_event_endpoint_no_json_body` - Handles missing JSON body for events
- `test_profile_endpoint_no_json_body` - Handles missing JSON body for profiles
- `test_eventxprofile_endpoint_no_json_body` - Handles missing JSON body for associations
- `test_invalid_json_format` - Handles malformed JSON
- `test_nonexistent_endpoint` - Returns 404 for non-existent endpoints
- `test_method_not_allowed` - Returns 405 for unsupported HTTP methods

### 2. `test_mock_event_api.py` (8 tests)
Tests database layer CRUD operations for events using mocked database sessions.

- `test_get_events` - Get all events
- `test_create_event_success` - Create event with valid data
- `test_create_event_missing_fields` - Validation for missing fields
- `test_create_event_invalid_datetime` - Validation for invalid datetime
- `test_create_event_end_before_start` - Business logic validation
- `test_delete_event_success` - Delete existing event
- `test_delete_event_not_found` - Delete non-existent event
- `test_delete_event_invalid_id` - Delete with invalid ID

### 3. `test_mock_eventxprofile_api.py` (8 tests)
Tests database layer CRUD operations for eventxprofile associations using mocked database sessions.

- `test_get_eventxprofiles` - Get all associations
- `test_create_eventxprofile_success` - Create association with valid data
- `test_create_eventxprofile_missing_fields` - Validation for missing fields
- `test_create_eventxprofile_invalid_ids` - Validation for invalid IDs
- `test_create_eventxprofile_not_found` - Create with non-existent event/profile
- `test_delete_eventxprofile_success` - Delete existing association
- `test_delete_eventxprofile_not_found` - Delete non-existent association
- `test_delete_eventxprofile_invalid_id` - Delete with invalid ID

### 4. `test_mock_profile_api.py` (6 tests)
Tests database layer CRUD operations for profiles using mocked database sessions.

- `test_get_profiles` - Get all profiles
- `test_create_profile_success` - Create profile with valid data
- `test_create_profile_missing_name` - Validation for missing name
- `test_delete_profile_success` - Delete existing profile
- `test_delete_profile_not_found` - Delete non-existent profile
- `test_delete_profile_invalid_id` - Delete with invalid ID

### 5. `unit/test_calendar_flow.py` (1 test)
Tests the calendar service integration.

- `test_get_full_calendar_current_month` - Calendar generation with events

### 6. `unit/test_converters.py` (12 tests)
Tests utility converter functions.

#### TestWeatherCodeToInfo (4 tests)
- `test_valid_weather_code` - Convert valid weather code
- `test_invalid_weather_code` - Handle invalid code
- `test_invalid_weather_code_negative` - Handle negative code
- `test_zero_weather_code` - Handle zero code

#### TestRoundTemperature (4 tests)
- `test_round_positive_temperature` - Round positive values
- `test_round_negative_temperature` - Round negative values
- `test_round_none_temperature` - Handle None values
- `test_round_zero_temperature` - Round zero

#### TestRoundTemperatures (4 tests)
- `test_round_multiple_temperatures` - Round list of temperatures
- `test_round_empty_list` - Handle empty list
- `test_round_negative_temperatures` - Round list with negatives

### 7. `unit/test_models.py` (15 tests)
Tests API data models.

#### TestWeatherCode (2 tests)
- `test_weather_code_creation` - Create weather code object
- `test_weather_code_to_dict` - Serialize to dictionary

#### TestCalendarDay (3 tests)
- `test_calendarDay_creation` - Create calendar day
- `test_is_empty_property` - Check empty day property
- `test_is_holiday_property` - Check holiday property

#### TestCalendarWeek (2 tests)
- `test_calendar_week_valid` - Create valid week
- `test_calendar_week_invalid_length` - Validate week length

#### TestWeatherReading (4 tests)
- `test_weather_reading_creation` - Create weather reading
- `test_weather_reading_to_dict` - Serialize to dictionary
- `test_weather_reading_with_none_temperature` - Handle None temperature
- `test_weather_reading_with_none_weather_code` - Handle None weather code

#### TestCalendarMonth (4 tests)
- `test_calendar_month_creation` - Create calendar month
- `test_calendar_month_default_current_day` - Default current day
- `test_calendar_month_to_dict` - Serialize to dictionary
- `test_calendar_month_with_holidays_and_weather` - With additional data
- `test_calendar_month_multiple_weeks` - Multiple weeks

### 8. `unit/test_weather_service.py` (4 tests)
Tests weather service functions.

#### TestGetCurrentWeather (2 tests)
- `test_get_current_weather_success` - Get current weather
- `test_get_current_weather_none_values` - Handle None values

#### TestGetHourlyForecastToday (1 test)
- `test_get_hourly_forecast_today` - Get hourly forecast

#### TestGetDailyForecast (1 test)
- `test_get_daily_forecast_success` - Get daily forecast

## Running Tests

### Run all tests
```bash
.venv/bin/python -m pytest tests/ -v
```

### Run specific test file
```bash
.venv/bin/python -m pytest tests/test_api_routes.py -v
```

### Run specific test class
```bash
.venv/bin/python -m pytest tests/test_api_routes.py::TestEventAPI -v
```

### Run specific test
```bash
.venv/bin/python -m pytest tests/test_api_routes.py::TestEventAPI::test_get_events_success -v
```

### Run with coverage
```bash
.venv/bin/python -m pytest tests/ --cov=. --cov-report=html
```

## Test Coverage Summary

| Component | Coverage |
|-----------|----------|
| API Routes (Flask endpoints) | ✅ Complete (40 tests) |
| Database Layer - Events | ✅ Complete (8 tests) |
| Database Layer - Profiles | ✅ Complete (6 tests) |
| Database Layer - EventXProfile | ✅ Complete (8 tests) |
| Utility Converters | ✅ Complete (12 tests) |
| API Models | ✅ Complete (15 tests) |
| Weather Service | ✅ Complete (4 tests) |
| Calendar Service | ✅ Complete (1 test) |

## Testing Approach

### API Route Tests
- Use Flask test client to make actual HTTP requests
- Mock database functions to isolate route logic
- Test all HTTP methods (GET, POST, PATCH, DELETE)
- Verify status codes and response formats
- Test error handling and edge cases

### Database Layer Tests
- Mock SQLAlchemy Session to avoid database dependencies
- Test CRUD operations independently
- Verify input validation
- Test error conditions
- Ensure proper error messages and status codes

### Unit Tests
- Test individual functions in isolation
- Use fixtures for test data
- Test edge cases and boundary conditions
- Verify data transformations

## Status Code Standards

All API endpoints follow consistent HTTP status code patterns:

- **200 OK** - Successful GET, PATCH, DELETE operations
- **201 Created** - Successful POST operations
- **400 Bad Request** - Validation errors, invalid input
- **404 Not Found** - Resource not found
- **405 Method Not Allowed** - Unsupported HTTP method
- **415 Unsupported Media Type** - Missing/invalid content type
- **500 Internal Server Error** - Unexpected server errors

## Continuous Integration

All tests must pass before merging code changes. The test suite is designed to:
- Run quickly (< 1 second)
- Be independent (no test depends on another)
- Be deterministic (same input = same output)
- Be isolated (use mocks, no external dependencies)
