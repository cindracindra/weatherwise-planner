"""
WeatherWise Planner Flask Application

This is the main application file using Flask factory pattern with Blueprints.
"""

import logging
import os
import secrets
from datetime import timedelta
from urllib.parse import urlsplit

from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Import blueprints
from routes.auth_routes import auth_bp
from routes.web_routes import web_bp
from routes.api_routes import api_bp
from utils.auth import (
    init_google, is_safe_next, login_manager, require_login,
)

load_dotenv()


def _secret_key() -> str:
    """The key that signs session cookies. It comes from the environment
    (.env locally, Render's settings in production) and is never in git.

    Production refuses to start without one. Elsewhere a random key is made
    for this run, which works but signs everyone out on every restart."""
    key = os.getenv("SECRET_KEY")
    if key:
        return key
    if os.getenv("RENDER"):
        raise RuntimeError("SECRET_KEY must be set in production.")
    logging.getLogger(__name__).warning(
        "SECRET_KEY not set; using a temporary key. Add one to .env."
    )
    return secrets.token_hex(32)


def _form_expired(error):
    """A form arrived without a valid CSRF token: most often a page left
    open across a sign-out, occasionally another site's forged form.
    Nothing is changed; the visitor is sent back to try again."""
    flash("That form had expired. Please try again.", "error")
    back = urlsplit(request.referrer or "")
    target = back.path + (f"?{back.query}" if back.query else "")
    if back.netloc == request.host and is_safe_next(target):
        return redirect(target)
    return redirect(url_for("web.homepage"))


def create_app(config_name="default"):
    """
    Application factory function.

    Args:
        config_name: Configuration name (default, testing, production)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Sessions: a signed cookie holding only the user id
    app.secret_key = _secret_key()
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,      # page scripts can't read it
        SESSION_COOKIE_SAMESITE="Lax",     # not sent with other sites' forms
        SESSION_COOKIE_SECURE=bool(os.getenv("RENDER")),  # HTTPS only live
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        # CSRF tokens last as long as the session, so a form left open
        # for a while still works
        WTF_CSRF_TIME_LIMIT=None,
    )

    # Render receives HTTPS and passes requests on as HTTP; trust its
    # X-Forwarded-Proto/Host headers so the app builds https:// links
    # (Google's redirect address must match exactly)
    if os.getenv("RENDER"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Who is signed in, and Google as a way to sign in
    login_manager.init_app(app)
    init_google(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    # Every page and API call needs a signed-in user (sign-in pages and
    # static files excepted; see require_login)
    app.before_request(require_login)

    # CSRF: every form post must carry the hidden token from our own page.
    # The JSON API is exempt: a browser won't send JSON, PATCH or DELETE
    # to it from another site without a CORS approval this app never gives.
    csrf = CSRFProtect(app)
    csrf.exempt(api_bp)
    app.register_error_handler(CSRFError, _form_expired)

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
