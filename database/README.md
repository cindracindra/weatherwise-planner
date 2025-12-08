# Database Module

The database layer provides a clean interface for all database operations using SQLAlchemy ORM. This module handles CRUD operations, data validation, serialization, and error handling for all database entities.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Module Files](#module-files)
- [Response Format](#response-format)
- [CRUD Operations](#crud-operations)
- [Validation & Error Handling](#validation--error-handling)
- [Usage Examples](#usage-examples)
- [Testing](#testing)

---

## Overview

### Purpose

The database module serves as the **data access layer** between Flask routes and the PostgreSQL database. It:

- ✅ Performs CRUD operations using SQLAlchemy ORM
- ✅ Validates input data and IDs
- ✅ Serializes database objects to JSON-compatible dictionaries
- ✅ Returns standardized responses with status codes
- ✅ Handles database errors gracefully
- ✅ Manages database sessions and transactions

### Technology Stack

- **ORM:** SQLAlchemy 2.0.44
- **Database:** PostgreSQL
- **Driver:** psycopg2-binary
- **Models:** Located in `models/db_models/`

---

## Architecture

```
database/
├── __init__.py              # Module initialization
├── engine.py                # Database engine configuration
├── db_event.py              # Event CRUD operations
├── db_profile.py            # Profile CRUD operations
├── db_eventxprofile.py      # Event-Profile association CRUD
├── db_composite.py          # Complex multi-table queries
└── sql_scripts/             # SQL schema and migrations
    └── SQL_command.sql
```

### Layered Architecture

```
┌─────────────────────────────────────────┐
│  Routes Layer (routes/)                 │
│  - Handles HTTP requests                │
│  - Calls database functions             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Database Layer (database/)             │
│  - CRUD operations                      │
│  - Data validation                      │
│  - Serialization                        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  ORM Layer (SQLAlchemy)                 │
│  - SQL query generation                 │
│  - Transaction management               │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Database (PostgreSQL)                  │
└─────────────────────────────────────────┘
```

---

## Module Files

### `engine.py`

**Purpose:** Database connection configuration and engine creation.

**Key Components:**
```python
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Create database URL from environment variables
url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    host=os.getenv("PGHOST"),
    port=int(os.getenv("PGPORT", "5432")),
    database=os.getenv("PGDATABASE"),
)

# Create engine instance
engine = create_engine(url)
```

**Environment Variables Required:**
- `PGUSER` - Database username
- `PGPASSWORD` - Database password
- `PGHOST` - Database host
- `PGPORT` - Database port (default: 5432)
- `PGDATABASE` - Database name

---

### `db_event.py`

**Purpose:** CRUD operations for Event entities.

**Functions:**

| Function | Method | Description | Returns |
|----------|--------|-------------|---------|
| `get_events()` | GET | Get all events | `(Response, int)` |
| `get_event_by_id(eventid)` | GET | Get event by ID | `(Response, int)` |
| `create_event(data)` | POST | Create new event | `(Response, int)` |
| `update_event(eventid, data)` | PATCH | Update existing event | `(Response, int)` |
| `delete_event(eventid)` | DELETE | Delete event | `(Response, int)` |

**Event Schema:**
```python
{
    "id": int,              # Auto-generated
    "name": str,            # Required
    "start_time": str,      # Required, ISO 8601 format
    "end_time": str,        # Required, ISO 8601 format
    "location": str         # Required
}
```

**Validation Rules:**
- All fields are required
- `start_time` and `end_time` must be valid ISO 8601 datetime strings
- `end_time` must be after `start_time`
- `eventid` must be a positive integer

---

### `db_profile.py`

**Purpose:** CRUD operations for Profile entities.

**Functions:**

| Function | Method | Description | Returns |
|----------|--------|-------------|---------|
| `get_profiles()` | GET | Get all profiles | `(Response, int)` |
| `get_profile_by_id(profileid)` | GET | Get profile by ID | `(Response, int)` |
| `create_profile(data)` | POST | Create new profile | `(Response, int)` |
| `delete_profile(profileid)` | DELETE | Delete profile | `(Response, int)` |

**Profile Schema:**
```python
{
    "id": int,      # Auto-generated
    "name": str     # Required
}
```

**Validation Rules:**
- `name` is required
- `profileid` must be a positive integer

---

### `db_eventxprofile.py`

**Purpose:** CRUD operations for Event-Profile associations (many-to-many).

**Functions:**

| Function | Method | Description | Returns |
|----------|--------|-------------|---------|
| `get_eventxprofiles()` | GET | Get all associations | `(Response, int)` |
| `get_eventxprofile_by_id(id)` | GET | Get association by ID | `(Response, int)` |
| `create_eventxprofile(data)` | POST | Create association | `(Response, int)` |
| `delete_eventxprofile(id)` | DELETE | Delete association | `(Response, int)` |

**EventXProfile Schema:**
```python
{
    "id": int,          # Auto-generated
    "eventid": int,     # Required, foreign key to Event
    "profileid": int    # Required, foreign key to Profile
}
```

**Validation Rules:**
- Both `eventid` and `profileid` are required
- Both must be positive integers
- Referenced event and profile must exist

---

### `db_composite.py`

**Purpose:** Complex queries involving multiple tables.

**Functions:**

| Function | Description | Returns |
|----------|-------------|---------|
| `get_events_by_profileid(profileid)` | Get all events for a profile | `(Response, int)` |
| `get_events_by_profileid_by_month(profileid, year, month)` | Get events for profile in specific month | `(Response, int)` |
| `create_event_and_profile_association(data)` | Create event and link to profile (atomic) | `(Response, int)` |
| `delete_event_and_profile_association(eventid, profileid)` | Delete event and its association | `(Response, int)` |

**Use Cases:**
- Homepage calendar display (events for a profile in a month)
- Event management page (all events for a profile)
- Atomic operations (create event + association in one transaction)

---

## Response Format

All database functions return a standardized response:

```python
(Response, int)  # Tuple of Flask Response object and status code
```

**Response JSON Structure:**
```json
{
  "statusCode": 200,
  "statusMessage": "Success message",
  "data": {
    // Response data here
  }
}
```

### Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST (create) |
| 400 | Bad Request | Validation error, missing fields |
| 404 | Not Found | Entity not found by ID |
| 500 | Internal Server Error | Database error, unexpected exception |

### Success Response Examples

**GET all entities:**
```json
{
  "statusCode": 200,
  "statusMessage": "Events retrieved successfully",
  "data": {
    "events": [
      {
        "id": 1,
        "name": "Team Meeting",
        "start_time": "2025-12-20T10:00:00",
        "end_time": "2025-12-20T11:00:00",
        "location": "Room 101"
      }
    ]
  }
}
```

**GET single entity:**
```json
{
  "statusCode": 200,
  "statusMessage": "Event retrieved successfully",
  "data": {
    "id": 1,
    "name": "Team Meeting",
    "start_time": "2025-12-20T10:00:00",
    "end_time": "2025-12-20T11:00:00",
    "location": "Room 101"
  }
}
```

**CREATE entity:**
```json
{
  "statusCode": 201,
  "statusMessage": "Event created successfully",
  "data": {
    "id": 123,
    "name": "New Event",
    ...
  }
}
```

### Error Response Examples

**Validation Error (400):**
```json
{
  "statusCode": 400,
  "statusMessage": "Validation error",
  "data": {
    "error": "Missing required fields: name, start_time"
  }
}
```

**Not Found (404):**
```json
{
  "statusCode": 404,
  "statusMessage": "Not found",
  "data": {
    "error": "Event with id 999 not found."
  }
}
```

**Server Error (500):**
```json
{
  "statusCode": 500,
  "statusMessage": "Internal server error",
  "data": {
    "error": "Database connection failed"
  }
}
```

---

## CRUD Operations

### Events

#### Create Event
```python
from database.db_event import create_event

data = {
    "name": "Sprint Planning",
    "start_time": "2025-12-20T10:00:00",
    "end_time": "2025-12-20T12:00:00",
    "location": "Conference Room A"
}

response, status_code = create_event(data)
```

#### Get All Events
```python
from database.db_event import get_events

response, status_code = get_events()
json_data = response.get_json()
events = json_data["data"]["events"]
```

#### Get Event by ID
```python
from database.db_event import get_event_by_id

response, status_code = get_event_by_id(1)
```

#### Update Event
```python
from database.db_event import update_event

data = {
    "name": "Updated Meeting",
    "location": "Room 202"
}

response, status_code = update_event(1, data)
```

#### Delete Event
```python
from database.db_event import delete_event

response, status_code = delete_event(1)
```

---

### Profiles

#### Create Profile
```python
from database.db_profile import create_profile

data = {"name": "John Doe"}
response, status_code = create_profile(data)
```

#### Get All Profiles
```python
from database.db_profile import get_profiles

response, status_code = get_profiles()
json_data = response.get_json()
profiles = json_data["data"]["profiles"]
```

#### Delete Profile
```python
from database.db_profile import delete_profile

response, status_code = delete_profile(1)
```

---

### Event-Profile Associations

#### Create Association
```python
from database.db_eventxprofile import create_eventxprofile

data = {
    "eventid": 5,
    "profileid": 3
}

response, status_code = create_eventxprofile(data)
```

#### Get All Associations
```python
from database.db_eventxprofile import get_eventxprofiles

response, status_code = get_eventxprofiles()
```

---

### Composite Operations

#### Get Events for Profile (Specific Month)
```python
from database.db_composite import get_events_by_profileid_by_month

response, status_code = get_events_by_profileid_by_month(
    profileid=3,
    year=2025,
    month=12
)
```

#### Create Event and Association (Atomic)
```python
from database.db_composite import create_event_and_profile_association

data = {
    "name": "Team Sync",
    "start_time": "2025-12-20T14:00:00",
    "end_time": "2025-12-20T15:00:00",
    "location": "Zoom",
    "profileid": 3
}

response, status_code = create_event_and_profile_association(data)
```

---

## Validation & Error Handling

### Input Validation

The database layer uses utility functions from `utils/request.py`:

**`validate_id(value)`**
- Ensures ID is a positive integer
- Returns validated ID or `StatusCode.BAD_REQUEST.value`

**`validate_required_fields(data, required_fields)`**
- Checks all required fields are present and non-empty
- Returns error message or None

**`parse_datetime(value)`**
- Parses ISO 8601 datetime string
- Returns datetime object or error message

**`validate_datetime_range(start, end)`**
- Ensures end_time is after start_time
- Returns error message or None

**`normalize_data(data)`**
- Converts ImmutableMultiDict (from forms) to dict
- Ensures consistent data format

### Error Handling Pattern

All database functions follow this pattern:

```python
def operation() -> Tuple[Response, int]:
    try:
        # 1. Validate input
        validated_id = validate_id(id)
        if validated_id == StatusCode.BAD_REQUEST.value:
            return build_response(
                StatusCode.BAD_REQUEST,
                {"error": "Invalid ID"}
            )
        
        # 2. Perform database operation
        with Session(engine) as session:
            # ... database logic ...
            session.commit()
        
        # 3. Return success response
        return build_response(StatusCode.OK, data)
        
    except Exception as e:
        # 4. Handle unexpected errors
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR,
            {"error": str(e)}
        )
```

### Session Management

- Uses **context managers** for automatic session cleanup
- Sessions are **short-lived** (created and closed per operation)
- **Automatic rollback** on exceptions
- **Thread-safe** session handling

```python
with Session(engine) as session:
    # Session automatically closes after this block
    event = session.get(Event, id)
    session.add(new_event)
    session.commit()
# Session closed here, even if exception occurs
```

---

## Usage Examples

### From Flask Route

```python
from flask import Blueprint, request
from database.db_event import create_event, get_events

api_bp = Blueprint('api', __name__)

@api_bp.route("/api/events", methods=["GET"])
def api_get_events():
    response, status_code = get_events()
    return response

@api_bp.route("/api/events", methods=["POST"])
def api_create_event():
    data = request.json
    response, status_code = create_event(data)
    return response
```

### Error Handling in Routes

```python
@web_bp.route("/")
def homepage():
    response, status_code = get_profiles()
    json_data = response.get_json()
    
    # Check for errors
    if json_data.get("statusCode") != 200:
        flash(f'Error: {json_data["data"]["error"]}', "error")
        profiles = []
    else:
        profiles = json_data["data"]["profiles"]
    
    return render_template("index.html", profiles=profiles)
```

---

## Testing

### Unit Tests

Located in `tests/database/`:

- `test_db_event.py` - Event CRUD tests
- `test_db_profile.py` - Profile CRUD tests
- `test_db_eventxprofile.py` - Association CRUD tests

**Run tests:**
```bash
# All database tests
pytest tests/database/ -v

# Specific test file
pytest tests/database/test_db_event.py -v

# With coverage
pytest tests/database/ --cov=database --cov-report=html
```

### Test Example

```python
def test_create_event(mock_session):
    data = {
        "name": "Test Event",
        "start_time": "2025-12-20T10:00:00",
        "end_time": "2025-12-20T11:00:00",
        "location": "Test Room"
    }
    
    response, status_code = create_event(data)
    json_data = response.get_json()
    
    assert json_data["statusCode"] == 201
    assert json_data["data"]["name"] == "Test Event"
```

### Manual Testing with HTTPie

See `API_TESTING_HTTPIE.md` for comprehensive HTTP testing examples.

```bash
# Create event
http POST localhost:5000/api/events \
  name="Test Event" \
  start_time="2025-12-20T10:00:00" \
  end_time="2025-12-20T11:00:00" \
  location="Test Room"

# Get all events
http GET localhost:5000/api/events
```

---

## Best Practices

### ✅ Do's

- **Use sessions as context managers** - Ensures automatic cleanup
- **Validate all inputs** - Use validation utilities
- **Return standardized responses** - Use `build_response()`
- **Handle exceptions** - Always wrap in try-except
- **Use transactions** - Group related operations
- **Test all CRUD operations** - Write comprehensive tests

### ❌ Don'ts

- **Don't keep sessions open** - Use short-lived sessions
- **Don't expose raw exceptions** - Wrap in custom error messages
- **Don't skip validation** - Always validate IDs and required fields
- **Don't mix business logic** - Keep database layer pure (no business logic)
- **Don't hardcode values** - Use environment variables for config

---

## Database Schema

See `diagrams/db-schema.png` for ERD.

**Tables:**

1. **event**
   - `id` (Primary Key)
   - `name` (VARCHAR)
   - `start_time` (TIMESTAMP)
   - `end_time` (TIMESTAMP)
   - `location` (VARCHAR)

2. **profile**
   - `id` (Primary Key)
   - `name` (VARCHAR)

3. **eventxprofile**
   - `id` (Primary Key)
   - `eventid` (Foreign Key → event.id)
   - `profileid` (Foreign Key → profile.id)

---

## Related Documentation

- **API Routes:** `routes/README.md`
- **Models:** `models/db_models/`
- **Utilities:** `utils/request.py`, `utils/response.py`
- **API Testing:** `API_TESTING_HTTPIE.md`

---

**Last Updated:** December 8, 2025  
**Database:** PostgreSQL  
**ORM:** SQLAlchemy 2.0.44  
**Python:** 3.14
