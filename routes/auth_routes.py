"""Sign-in and sign-out pages."""

from authlib.integrations.base_client import OAuthError
from flask import (
    Blueprint, abort, flash, redirect, render_template, request, session,
    url_for,
)
from flask_login import current_user, login_user, logout_user

from utils.auth import (
    dev_login_enabled, get_or_create_dev_user, google_client,
    google_configured, is_safe_next, upsert_google_user,
)
from utils.demo import create_demo_user, delete_demo_user

auth_bp = Blueprint("auth", __name__)


def _start_session(user, next_url=None, lasting=True):
    """Sign `user` in on a fresh session and send them on their way."""
    # A fresh session on sign-in, so nothing from before carries over
    session.clear()
    login_user(user)
    # Real accounts keep the session for PERMANENT_SESSION_LIFETIME
    # (30 days), renewed on every visit; a demo's ends with the browser
    session.permanent = lasting
    if is_safe_next(next_url):
        return redirect(next_url)
    return redirect(url_for("web.homepage"))


def _back_to_sign_in(message):
    flash(message, "error")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login")
def login():
    """The sign-in page."""
    if current_user.is_authenticated:
        target = request.args.get("next")
        if is_safe_next(target):
            return redirect(target)
        return redirect(url_for("web.homepage"))
    return render_template(
        "login.html",
        next=request.args.get("next", ""),
        google=google_configured(),
        dev_login=dev_login_enabled(),
    )


@auth_bp.route("/login/google")
def login_google():
    """Step 1 of Google sign-in: send the visitor to Google.

    Authlib stores a random `state` and `nonce` in the session first; the
    callback checks both, so a reply that didn't start here is refused."""
    client = google_client()
    if client is None:
        abort(404)
    next_url = request.args.get("next")
    session["next"] = next_url if is_safe_next(next_url) else None
    return client.authorize_redirect(
        url_for("auth.google_callback", _external=True)
    )


@auth_bp.route("/auth/google/callback")
def google_callback():
    """Step 2: Google sends the visitor back here with a one-time code."""
    client = google_client()
    if client is None:
        abort(404)
    if request.args.get("error"):
        # For example access_denied, when the visitor pressed Cancel
        return _back_to_sign_in("Sign-in was cancelled.")

    try:
        # Checks state, swaps the code for tokens (server to server, with
        # the client secret), and verifies the ID token's signature/nonce
        token = client.authorize_access_token()
    except OAuthError:
        return _back_to_sign_in(
            "Google sign-in couldn't be completed. Please try again."
        )

    info = token.get("userinfo") or {}
    if not info.get("sub"):
        return _back_to_sign_in(
            "Google didn't confirm who you are. Please try again."
        )
    if not info.get("email_verified"):
        return _back_to_sign_in(
            "Your Google email address isn't verified yet."
        )

    next_url = session.pop("next", None)
    return _start_session(upsert_google_user(info), next_url)


@auth_bp.route("/login/dev", methods=["POST"])
def login_dev():
    """Local-only test sign-in, never available on Render."""
    if not dev_login_enabled():
        abort(404)
    return _start_session(get_or_create_dev_user(), request.form.get("next"))


@auth_bp.route("/login/demo", methods=["POST"])
def login_demo():
    """Try the demo: a fresh throwaway account with sample events."""
    return _start_session(create_demo_user(), lasting=False)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Sign out: forget the user and clear the session. A demo account is
    deleted on the spot, as nobody can sign back into it."""
    is_demo = getattr(current_user, "is_demo", False)
    demo_id = current_user.id if is_demo else None
    logout_user()
    session.clear()
    if demo_id is not None:
        delete_demo_user(demo_id)
        flash("Thanks for trying WeatherWise. The demo calendar is deleted.",
              "success")
    else:
        flash("You're signed out.", "success")
    return redirect(url_for("auth.login"))
