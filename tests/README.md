# Tests

```bash
pytest tests/
```

The suite needs **no database and no network**: database sessions, Google and the weather APIs are replaced with stand-ins, so it runs the same locally and on GitHub Actions. The app needs a `SECRET_KEY` to start; locally it comes from `.env`, and the CI workflow sets a throwaway one.

| File | Covers |
|---|---|
| `database/test_db_event.py` | Event CRUD, and ownership: another account's event is not found, can't be changed or deleted, and the owner can't be set or changed; errors don't leak details |
| `routes/test_web_routes.py` | The calendar and events pages and their forms, scoped to the signed-in account |
| `routes/test_api_routes.py` | The JSON API calls the database for the signed-in account; removed profile endpoints are gone |
| `routes/test_auth.py` | Signed-out redirects and `401`s, a walk over every route, sessions and cookie settings, sign-out, safe `?next=`, Google sign-in (success, cancel, bad reply, unverified email, Google unreachable, double first sign-in), and the `SECRET_KEY` rule |
| `routes/test_csrf.py` | With CSRF on: forged forms and other sessions' tokens are refused, our own forms work, the API is unaffected, every form carries a token |
| `routes/test_demo.py` | Try the demo: fresh accounts with sample events around today, deletion on sign-out, the one-day expiry, the 200 cap, and that demo deletes never touch real accounts |
| `unit/` | Weather and calendar services, models, converters, and today's timeline using London's date |

Conventions:

- Page and API tests turn sign-in off (`LOGIN_DISABLED`) and CSRF off (`WTF_CSRF_ENABLED = False`); `test_auth.py` and `test_csrf.py` test those with them on.
- Database code is tested by patching `Session`; routes are tested by patching the `database` functions they call.
