"""API routes blueprint for REST API endpoints.

Every endpoint works on the current account's events only.
"""

from flask import Blueprint, request

from database.db_event import (
    get_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
)
from utils.current_user import current_user_id

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ========== Event APIs ==========

@api_bp.route("/events", methods=["GET"])
def api_get_events():
    """GET the account's events."""
    return get_events(current_user_id())


@api_bp.route("/events/<int:eventid>", methods=["GET"])
def api_get_event_by_id(eventid):
    """GET one of the account's events."""
    return get_event_by_id(eventid, current_user_id())


@api_bp.route("/events", methods=["POST"])
def api_create_event():
    """POST create a new event."""
    return create_event(request.json, current_user_id())


@api_bp.route("/events/<int:eventid>", methods=["PATCH"])
def api_update_event(eventid):
    """PATCH update one of the account's events."""
    return update_event(eventid, request.json, current_user_id())


@api_bp.route("/events/<int:eventid>", methods=["DELETE"])
def api_delete_event(eventid):
    """DELETE one of the account's events."""
    return delete_event(eventid, current_user_id())
