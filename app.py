"""
WeatherWise Planner Flask Application

This is the main application file using Flask factory pattern with Blueprints.
"""

import logging
import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask

# Import blueprints
from routes.auth_routes import auth_bp
from routes.web_routes import web_bp
from routes.api_routes import api_bp
from utils.auth import login_manager, require_login

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
    )

    # Who is signed in
    login_manager.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    # Every page and API call needs a signed-in user (sign-in pages and
    # static files excepted; see require_login)
    app.before_request(require_login)

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
