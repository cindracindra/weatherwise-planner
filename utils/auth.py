"""Sign-in plumbing: who is signed in, and what happens when nobody is.

How a request finds its user:
  1. The browser sends the session cookie with every request.
  2. Flask checks the cookie's signature with SECRET_KEY; a tampered
     cookie is ignored, as if there were none.
  3. Flask-Login reads the user id stored in it and calls load_user(),
     which fetches that AppUser from the database.
  4. The route reads it as `current_user`.
"""

import os
from typing import Optional
from urllib.parse import urlsplit

from flask import current_app, jsonify, redirect, request, url_for
from flask_login import LoginManager, current_user
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.engine import engine
from models.db_models.user import AppUser

login_manager = LoginManager()

# The account the local-only test sign-in uses
DEV_SUB = "local-dev"

# Blueprints that need a signed-in user
PROTECTED = {"web", "api"}


@login_manager.user_loader
def load_user(user_id: str) -> Optional[AppUser]:
    """Step 3 above: the user id from the cookie -> the account, or None
    (for example if the account was deleted), which means signed out."""
    try:
        with Session(engine) as session:
            user = session.get(AppUser, int(user_id))
            if user is not None:
                session.expunge(user)  # usable after the session closes
            return user
    except (ValueError, TypeError):
        return None


def is_safe_next(target: Optional[str]) -> bool:
    """Only follow ?next= to a page on this site. Without this check a
    link like /login?next=https://evil.example would bounce people who
    just signed in to another site (an "open redirect")."""
    if not target or "\\" in target:
        # Browsers read "/\evil.example" like "//evil.example"
        return False
    parts = urlsplit(target)
    return not parts.scheme and not parts.netloc and target.startswith("/")


def require_login():
    """Runs before every request. Only the web pages and the API are
    protected; the sign-in pages and static files are open.

    Signed out: pages redirect to the sign-in page (remembering where you
    were going), and the API answers 401 with a JSON error.
    """
    if request.blueprint not in PROTECTED:
        return None
    if current_app.config.get("LOGIN_DISABLED"):
        return None
    if current_user.is_authenticated:
        return None
    if request.blueprint == "api":
        body = {"statusCode": 401, "statusMessage": "UNAUTHORIZED",
                "data": {"error": "Sign in to use the API."}}
        return jsonify(body), 401
    return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))


def dev_login_enabled() -> bool:
    """The local test sign-in exists only on a developer's machine: in debug
    mode (flask run --debug) or when a test turns it on, and never on Render
    (which sets the RENDER environment variable)."""
    if os.getenv("RENDER"):
        return False
    return bool(current_app.debug or current_app.config.get("DEV_LOGIN"))


def get_or_create_dev_user() -> AppUser:
    """The local developer account, created on first use."""
    with Session(engine) as session:
        user = session.execute(
            select(AppUser).where(AppUser.google_sub == DEV_SUB)
        ).scalar_one_or_none()
        if user is None:
            user = AppUser(google_sub=DEV_SUB, name="Local developer")
            session.add(user)
            session.commit()
            session.refresh(user)
        session.expunge(user)
        return user
