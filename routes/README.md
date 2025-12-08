# Routes Module

The routes layer handles HTTP requests and responses, connecting the web interface and REST API to the database layer. This module contains Flask Blueprints for both web pages and API endpoints.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Module Files](#module-files)
- [Web Routes](#web-routes)
- [API Routes](#api-routes)
- [Request/Response Flow](#requestresponse-flow)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)
- [Testing](#testing)

---

## Overview

### Purpose

The routes module provides:

- ✅ **Web Routes** (`web_routes.py`) - HTML pages for user interface
- ✅ **API Routes** (`api_routes.py`) - RESTful JSON API endpoints
- ✅ Request validation and parameter extraction
- ✅ Error handling and user feedback
- ✅ Integration with database layer and services

### Technology Stack

- **Framework:** Flask 3.1.2
- **Template Engine:** Jinja2 3.1.6
- **Blueprints:** Modular route organization
- **Sessions:** Flash messages for user feedback

---

## Architecture

```
routes/
├── __init__.py          # Module initialization
├── web_routes.py        # HTML pages (Blueprint: 'web')
└── api_routes.py        # REST API (Blueprint: 'api')
```

### Request Flow

```
┌────────────────────────────────────────┐
│  Client (Browser / HTTP Client)        │
└────────────────────────────────────────┘
                  ↓
┌────────────────────────────────────────┐
│  Flask Application                     │
└────────────────────────────────────────┘
                  ↓
┌─────────────┬──────────────────────────┐
│ web_routes  │  api_routes              │
│ (HTML)      │  (JSON)                  │
└─────────────┴──────────────────────────┘
                  ↓
┌────────────────────────────────────────┐
│  API / Database Modules                │
└────────────────────────────────────────┘
                  ↓
┌────────────────────────────────────────┐
│  PostgreSQL Database / External APIs   │
└────────────────────────────────────────┘
```

---

## Module Files

### `web_routes.py`

**Blueprint:** `web` (no URL prefix)

**Purpose:** Serves HTML pages for the web interface.

**Responsibilities:**

- Render Jinja2 templates
- Handle form submissions
- Manage user sessions and flash messages
- Integrate calendar, weather, and event data
- Provide user-friendly error messages

**Routes:** 3 pages

- `/` - Homepage with calendar
- `/management` - Event management page
- `/management/profile` - Profile management page

---

### `api_routes.py`

**Blueprint:** `api` (URL prefix: `/api`)

**Purpose:** Provides RESTful JSON API endpoints.

**Responsibilities:**

- Parse JSON request bodies
- Call database CRUD functions
- Return standardized JSON responses
- Handle API errors

**Routes:** 13 endpoints

- 5 Event endpoints
- 4 Profile endpoints
- 4 Event-Profile association endpoints

---

## Web Routes

### Route Definitions

| Route                 | Method    | Template                  | Description                       |
| --------------------- | --------- | ------------------------- | --------------------------------- |
| `/`                   | GET       | `index.html`              | Homepage with calendar and events |
| `/management`         | GET, POST | `management.html`         | Event management interface        |
| `/management/profile` | GET, POST | `management_profile.html` | Profile management interface      |

---

### Homepage (`/`)

**Purpose:** Display calendar with events for selected profile.

**Data Sources:**

1. **Profiles** - From `get_profiles()`
2. **Calendar Matrix** - From `get_full_calendar(year, month)`
3. **Hourly Weather** - From `get_hourly_forecast_today()`
4. **Monthly Events** - From `get_events_by_profileid_by_month()`

**Features:**

- Calendar view with current month
- Weather forecast integration
- Holiday highlighting
- Event display by day
- Profile selector dropdown

---

### Event Management (`/management`)

**Purpose:** Create, update, and delete events for a profile.

**Supported Functions:**

#### View Events

Displays all events for the selected profile.

#### Create Event

Creates new event and associates with profile.

**Form Fields:**

- `event-title` - Event name
- `event-start-date` - Start datetime (YYYY-MM-DDTHH:MM)
- `event-end-date` - End datetime (YYYY-MM-DDTHH:MM)
- `event-location` - Event location

#### Update Event

Updates existing event details.

**Form Fields:**

- `event-id` - Event ID to update
- `event-title` - New title
- `event-start-date` - New start time
- `event-end-date` - New end time
- `event-location` - New location

#### Delete Event

Removes event and its profile association.

**Form Fields:**

- `event-id` - Event ID to delete

---

### Profile Management (`/management/profile`)

**Purpose:** Create and delete user profiles.

**Supported Functions:**

#### View Profiles

Displays all existing profiles.

#### Create Profile

Creates a new profile.

**Form Fields:**

- `profile-name` - Profile name

#### Delete Profile

Removes a profile.

**Form Fields:**

- `profile-id` - Profile ID to delete

## API Routes

### Supported APIs

All API routes are prefixed with `/api`.

| Endpoint                   | Method | Description           |
| -------------------------- | ------ | --------------------- |
| `/api/events`              | GET    | Get all events        |
| `/api/events/<id>`         | GET    | Get event by ID       |
| `/api/events`              | POST   | Create event          |
| `/api/events/<id>`         | PATCH  | Update event          |
| `/api/events/<id>`         | DELETE | Delete event          |
| `/api/profiles`            | GET    | Get all profiles      |
| `/api/profiles/<id>`       | GET    | Get profile by ID     |
| `/api/profiles`            | POST   | Create profile        |
| `/api/profiles/<id>`       | DELETE | Delete profile        |
| `/api/event-profiles`      | GET    | Get all associations  |
| `/api/event-profiles/<id>` | GET    | Get association by ID |
| `/api/event-profiles`      | POST   | Create association    |
| `/api/event-profiles/<id>` | DELETE | Delete association    |

---

### Event API Endpoints

#### GET `/api/events`

```python
@api_bp.route("/events", methods=["GET"])
def api_get_events():
    """Get all events."""
    return get_events()
```

**Response:**

```json
{
  "statusCode": 200,
  "statusMessage": "Events retrieved successfully",
  "data": {
    "events": [...]
  }
}
```

#### POST `/api/events`

```python
@api_bp.route("/events", methods=["POST"])
def api_create_event():
    """Create new event."""
    data = request.json
    return create_event(data)
```

**Request Body:**

```json
{
  "name": "Team Meeting",
  "start_time": "2025-12-20T10:00:00",
  "end_time": "2025-12-20T11:00:00",
  "location": "Room 101"
}
```

---

### Profile API Endpoints

#### GET `/api/profiles`

```python
@api_bp.route("/profiles", methods=["GET"])
def api_get_profiles():
    """Get all profiles."""
    return get_profiles()
```

#### POST `/api/profiles`

```python
@api_bp.route("/profiles", methods=["POST"])
def api_create_profile():
    """Create new profile."""
    data = request.json
    return create_profile(data)
```

**Request Body:**

```json
{
  "name": "John Doe"
}
```

---

### Event-Profile Association Endpoints

#### POST `/api/event-profiles`

```python
@api_bp.route("/event-profiles", methods=["POST"])
def api_create_event_profile():
    """Create event-profile association."""
    data = request.json
    return create_eventxprofile(data)
```

**Request Body:**

```json
{
  "eventid": 5,
  "profileid": 3
}
```

---

## Request/Response Flow

### Web Routes Flow

```
1. User submits form
   ↓
2. Flask receives POST/PATCH/DELETE request
   ↓
3. Route extracts form data (request.form)
   ↓
4. Route calls database function
   ↓
5. Database returns (Response, int) tuple
   ↓
6. Route checks statusCode in response JSON
   ↓
7. Route displays flash message (success/error)
   ↓
8. Route renders template or redirects
```

### API Routes Flow

```
1. Client sends HTTP request with JSON body
   ↓
2. Flask receives request
   ↓
3. Route extracts JSON data (request.json)
   ↓
4. Route calls database function
   ↓
5. Database returns (Response, int) tuple
   ↓
6. Route returns Response (Flask auto-converts to HTTP response)
```

---

## Error Handling

### Web Routes Error Handling

**Pattern:**

```python
response, status_code = database_function(data)
json_data = response.get_json()

if json_data.get("statusCode") != expected_code:
    flash(f'Error: {json_data["data"]["error"]}', "error")
    # Handle error case
else:
    flash("Success message!", "success")
    # Handle success case
```

**Flash Message Categories:**

- `"success"` - Green success messages
- `"error"` - Red error messages
- `"warning"` - Yellow warning messages
- `"info"` - Blue information messages

**Example:**

```python
@web_bp.route("/management/profile", methods=["POST"])
def web_profile():
    if request.method == "POST":
        data = {"name": request.form.get("profile-name")}
        response, _ = create_profile(data)
        json_data = response.get_json()

        if json_data.get("statusCode") == 201:
            flash("Profile created successfully!", "success")
        else:
            error = json_data["data"].get("error", "Unknown error")
            flash(f"Error creating profile: {error}", "error")
```

---

### API Routes Error Handling

API routes rely on the database layer for error handling. They simply return the Response object:

```python
@api_bp.route("/events", methods=["POST"])
def api_create_event():
    data = request.json
    return create_event(data)  # Database handles all validation/errors
```

The database layer returns standardized responses with appropriate status codes.

---

## Usage Examples

### Calling from Python

```python
import requests

# Create event via API
response = requests.post(
    "http://localhost:5000/api/events",
    json={
        "name": "Team Sync",
        "start_time": "2025-12-20T14:00:00",
        "end_time": "2025-12-20T15:00:00",
        "location": "Zoom"
    }
)

print(response.json())
```

### Form Submission (HTML)

```html
<form method="POST" action="/management/profile">
  <input type="text" name="profile-name" required />
  <button type="submit">Create Profile</button>
</form>
```

### AJAX Request (JavaScript)

```javascript
// Create event via API
fetch("/api/events", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    name: "Meeting",
    start_time: "2025-12-20T10:00:00",
    end_time: "2025-12-20T11:00:00",
    location: "Room 101",
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

---

## Testing

### Manual Testing (Web Interface)

1. Start Flask development server:

```bash
flask run
```

2. Navigate to routes:

- Homepage: `http://localhost:5000/`
- Event Management: `http://localhost:5000/management?profileid=1`
- Profile Management: `http://localhost:5000/management/profile`

---

### API Testing with HTTPie

See `API_TESTING_HTTPIE.md` for comprehensive examples.

```bash
# Get all events
http GET localhost:5000/api/events

# Create event
http POST localhost:5000/api/events \
  name="Test Event" \
  start_time="2025-12-20T10:00:00" \
  end_time="2025-12-20T11:00:00" \
  location="Test Room"

# Update event
http PATCH localhost:5000/api/events/1 \
  name="Updated Title"

# Delete event
http DELETE localhost:5000/api/events/1
```

---

### Unit Testing

Located in `tests/routes/`:

- `test_api_routes.py` - API endpoint tests

**Run tests:**

```bash
# All route tests
pytest tests/routes/ -v

# Specific test file
pytest tests/routes/test_api_routes.py -v

# With coverage
pytest tests/routes/ --cov=routes --cov-report=html
```

**Example Test:**

```python
def test_api_create_event(client):
    response = client.post(
        "/api/events",
        json={
            "name": "Test Event",
            "start_time": "2025-12-20T10:00:00",
            "end_time": "2025-12-20T11:00:00",
            "location": "Test Room"
        }
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["statusCode"] == 201
    assert data["data"]["name"] == "Test Event"
```

---

## Best Practices

### ✅ Do's

- **Validate query parameters** - Check for required params
- **Use flash messages** - Provide user feedback
- **Check response statusCode** - Verify database operations succeeded
- **Handle missing data gracefully** - Provide empty lists/defaults
- **Use blueprints** - Keep routes organized
- **Extract reusable logic** - Use utility functions
- **Test all routes** - Write comprehensive tests

### ❌ Don'ts

- **Don't put business logic in routes** - Keep routes thin
- **Don't hardcode URLs** - Use `url_for()`
- **Don't ignore errors** - Always check statusCode
- **Don't trust user input** - Validate all form data
- **Don't expose sensitive info** - Handle errors gracefully
- **Don't skip CSRF protection** - Use Flask-WTF in production

---

## Route Registration

Routes are registered in `app.py`:

```python
from routes.web_routes import web_bp
from routes.api_routes import api_bp

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    return app
```

---

## Related Documentation

- **Database Layer:** `database/README.md`
- **API Testing:** `API_TESTING_HTTPIE.md`
- **Models:** `models/db_models/`
- **Services:** `services/calendar_service.py`, `services/weather_service.py`
- **Utilities:** `utils/datafeed.py`, `utils/helpers.py`, `utils/request.py`

---

## URL Reference

### Web Routes (HTML Pages)

| URL                       | Description            |
| ------------------------- | ---------------------- |
| `/`                       | Homepage with calendar |
| `/management?profileid=1` | Event management       |
| `/management/profile`     | Profile management     |

### API Routes (JSON Endpoints)

| URL                        | Methods            | Description             |
| -------------------------- | ------------------ | ----------------------- |
| `/api/events`              | GET, POST          | Events collection       |
| `/api/events/<id>`         | GET, PATCH, DELETE | Single event            |
| `/api/profiles`            | GET, POST          | Profiles collection     |
| `/api/profiles/<id>`       | GET, DELETE        | Single profile          |
| `/api/event-profiles`      | GET, POST          | Associations collection |
| `/api/event-profiles/<id>` | GET, DELETE        | Single association      |

---

**Last Updated:** December 8, 2025  
**Framework:** Flask 3.1.2  
**Blueprints:** 2 (web, api)  
**Total Routes:** 16 (3 web + 13 API)
