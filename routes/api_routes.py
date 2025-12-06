"""API routes blueprint for REST API endpoints."""

from flask import Blueprint, request

from database.db_event import (
    get_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
)
from database.db_profile import (
    get_profiles,
    get_profile_by_id,
    create_profile,
    delete_profile,
)
from database.db_eventxprofile import (
    get_eventxprofiles,
    get_eventxprofile_by_id,
    create_eventxprofile,
    delete_eventxprofile,
)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ========== Event APIs ==========

@api_bp.route("/events", methods=["GET"])
def api_get_events():
    """GET all events."""
    return get_events()


@api_bp.route("/events/<int:event_id>", methods=["GET"])
def api_get_event_by_id(event_id):
    """GET event by ID."""
    return get_event_by_id(event_id)


@api_bp.route("/events", methods=["POST"])
def api_create_event():
    """POST create new event."""
    data = request.json
    return create_event(data)


@api_bp.route("/events/<int:event_id>", methods=["PATCH"])
def api_update_event(event_id):
    """PATCH update event."""
    data = request.json
    return update_event(event_id, data)


@api_bp.route("/events/<int:event_id>", methods=["DELETE"])
def api_delete_event(event_id):
    """DELETE event."""
    return delete_event(event_id)


# ========== Profile APIs ==========

@api_bp.route("/profiles", methods=["GET"])
def api_get_profiles():
    """GET all profiles."""
    return get_profiles()


@api_bp.route("/profiles/<int:profile_id>", methods=["GET"])
def api_get_profile_by_id(profile_id):
    """GET profile by ID."""
    return get_profile_by_id(profile_id)


@api_bp.route("/profiles", methods=["POST"])
def api_create_profile():
    """POST create new profile."""
    data = request.json
    return create_profile(data)


@api_bp.route("/profiles/<int:profile_id>", methods=["DELETE"])
def api_delete_profile(profile_id):
    """DELETE profile."""
    return delete_profile(profile_id)


# ========== Event-Profile APIs ==========

@api_bp.route("/event-profiles", methods=["GET"])
def api_get_event_profiles():
    """GET all event-profile associations."""
    return get_eventxprofiles()


@api_bp.route("/event-profiles/<int:event_profile_id>", methods=["GET"])
def api_get_event_profile_by_id(event_profile_id):
    """GET event-profile association by ID."""
    return get_eventxprofile_by_id(event_profile_id)


@api_bp.route("/event-profiles", methods=["POST"])
def api_create_event_profile():
    """POST create new event-profile association."""
    data = request.json
    return create_eventxprofile(data)


@api_bp.route("/event-profiles/<int:event_profile_id>", methods=["DELETE"])
def api_delete_event_profile(event_profile_id):
    """DELETE event-profile association."""
    return delete_eventxprofile(event_profile_id)
