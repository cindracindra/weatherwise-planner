"""Sign-in and sign-out pages."""

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, session,
    url_for,
)
from flask_login import current_user, login_user, logout_user

from utils.auth import dev_login_enabled, get_or_create_dev_user, is_safe_next

auth_bp = Blueprint("auth", __name__)


def _signed_in_redirect():
    """After signing in: back to where the person was going, or home."""
    target = request.values.get("next")
    if is_safe_next(target):
        return redirect(target)
    return redirect(url_for("web.homepage"))


@auth_bp.route("/login")
def login():
    """The sign-in page."""
    if current_user.is_authenticated:
        return _signed_in_redirect()
    return render_template(
        "login.html",
        next=request.args.get("next", ""),
        dev_login=dev_login_enabled(),
    )


@auth_bp.route("/login/dev", methods=["POST"])
def login_dev():
    """Local-only test sign-in, until Google sign-in exists (step 4)."""
    if not dev_login_enabled():
        abort(404)
    # A fresh session on sign-in, so nothing from before carries over
    session.clear()
    login_user(get_or_create_dev_user())
    # Keep the session for PERMANENT_SESSION_LIFETIME (30 days), renewed
    # on every visit, instead of ending when the browser closes
    session.permanent = True
    return _signed_in_redirect()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Sign out: forget the user and clear the session."""
    logout_user()
    session.clear()
    flash("You're signed out.", "success")
    return redirect(url_for("auth.login"))
