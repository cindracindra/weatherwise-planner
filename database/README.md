# Database

The data layer between the routes and PostgreSQL, using SQLAlchemy.

| File | What it does |
|---|---|
| `engine.py` | Builds the SQLAlchemy engine from the `PG*` environment variables |
| `db_event.py` | Create, read, update and delete events, always for one account |
| `sql_scripts/SQL_command.sql` | Builds the schema from scratch, with sample data (**deletes everything**) |
| `sql_scripts/001_accounts.sql` | Migration: accounts and event ownership (see below) |

Models live in `models/db_models/`: `AppUser` (`user.py`) and `Event` (`event.py`). Account helpers (Google, the local developer account, demos) are in `utils/auth.py` and `utils/demo.py`.

## Schema

- **`app_user`**: one row per person. `google_sub` is Google's permanent account id (unique, empty for demo accounts), plus `email`, `name`, `is_demo` and `created_at`.
- **`event`**: `name`, `start_time`, `end_time`, `location` and `user_id`. Every event belongs to exactly one account; deleting the account deletes its events (`ON DELETE CASCADE`).

Times are stored without a time zone, in London time.

## `db_event.py`

Every function takes the id of the account the request is for:

| Function | Returns |
|---|---|
| `get_events(user_id, year=None, month=None)` | The account's events, oldest first; with `year` and `month`, only those starting that month |
| `get_event_by_id(eventid, user_id)` | One event |
| `create_event(data, user_id)` | The new event (`201`) |
| `update_event(eventid, data, user_id)` | The changed event |
| `delete_event(eventid, user_id)` | A confirmation |

Rules every function follows:

- **Ownership:** an event that belongs to another account is reported exactly like one that doesn't exist (`404`). The owner is never taken from `data`, and can't be changed.
- **Validation:** a non-integer id is `400`; `create_event` needs all four fields; times must be ISO 8601 and the end must be after the start.
- **Errors:** unexpected failures (for example the database being down) are logged on the server and answered with a plain `500` message, never the raw exception.

All functions return `(response, status)` from `utils.response.build_response`: `{"statusCode", "statusMessage", "data"}`.

## Changing the schema

A database that's already in use is changed with **numbered migration scripts**, run in order, each safe to run more than once:

```bash
psql "$DATABASE_URL" -f database/sql_scripts/001_accounts.sql
```

`001_accounts.sql` adds `app_user` and `event.user_id`, and removes the old `profile` and `eventxprofile` tables. Events from before accounts existed have no owner and are discarded; this only happens the first time it runs.

Keep `SQL_command.sql` in step with the migrations so a fresh database matches a migrated one.
