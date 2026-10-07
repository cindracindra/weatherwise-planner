# Routes

Flask blueprints that turn HTTP requests into pages and JSON. Data access lives in `database/`, weather and holidays in `services/`, sign-in plumbing in `utils/auth.py`.

| File | Blueprint | What it serves |
|---|---|---|
| `auth_routes.py` | `auth` | Sign-in page, Google sign-in, the demo, sign-out |
| `web_routes.py` | `web` | The calendar and events pages, and their forms |
| `api_routes.py` | `api` | The JSON API under `/api` |

## Who can reach what

`utils.auth.require_login` runs before every request. The `web` and `api` blueprints need a signed-in user; `auth` and static files are open.

- Signed out, a **page** redirects to `/login?next=<where you were going>`. For a form submission, `next` is the page the form was on.
- Signed out, the **API** answers `401` with a JSON error.
- Routes ask for the account with `current_user_id()` (`utils/current_user.py`) and pass it to every database call. Nothing a browser sends can choose whose data is read or changed.

`tests/routes/test_auth.py::test_every_page_and_api_route_needs_sign_in` walks every route, so a new route added without protection fails the tests.

## Sign-in (`auth_routes.py`)

| Route | Method | What it does |
|---|---|---|
| `/login` | GET | Sign-in page: Google, Try the demo, and (debug only) local developer |
| `/login/google` | GET | Starts Google sign-in: stores `state`/`nonce`, redirects to Google |
| `/auth/google/callback` | GET | Google returns here; verifies the reply, finds or creates the account, signs in |
| `/login/demo` | POST | Creates a fresh demo account with sample events and signs in |
| `/login/dev` | POST | Local developer sign-in (debug mode only, never on Render) |
| `/logout` | POST | Signs out; a demo account is deleted on the spot |

Every sign-in starts a fresh session. Real accounts keep it for 30 days; a demo's ends when the browser closes. `?next=` is only followed to paths on this site (`is_safe_next`).

## Pages (`web_routes.py`)

| Route | Method | What it does |
|---|---|---|
| `/` | GET | Today's weather, the hourly strip with today's events, and the month |
| `/reload` | GET | Back to `/` (the refresh button) |
| `/management/event` | GET | All your events, and the form to add or change one (`?selected_eventid=` picks one) |
| `/management/event/load` | POST | Selects an event to change |
| `/management/event/create` | POST | Adds an event |
| `/management/event/update` | POST | Changes an event |
| `/management/event/delete` | POST | Deletes an event |

Form posts carry a CSRF token (Flask-WTF). A post without a valid one changes nothing and sends the visitor back with "That form had expired". Results come back as a redirect with `?reqHttpCode=` so the page can show a success or error message. Missing or malformed times are treated as a bad request, not an error page.

## API (`api_routes.py`)

| Route | Method | Body |
|---|---|---|
| `/api/events` | GET | |
| `/api/events/<id>` | GET | |
| `/api/events` | POST | JSON `name`, `start_time`, `end_time`, `location` (ISO 8601 times) |
| `/api/events/<id>` | PATCH | JSON with any of the fields above |
| `/api/events/<id>` | DELETE | |

All responses use `{"statusCode", "statusMessage", "data"}` (`utils/response.py`). The API is exempt from CSRF tokens: browsers won't send JSON, PATCH or DELETE to it from another site without a CORS approval this app never gives.
