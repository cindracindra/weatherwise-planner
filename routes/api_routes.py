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


@api_bp.route("/events/<int:eventid>", methods=["GET"])
def api_get_event_by_id(eventid):
    """GET event by ID."""
    return get_event_by_id(eventid)


@api_bp.route("/events", methods=["POST"])
def api_create_event():
    """POST create new event."""
    data = request.json
    return create_event(data)


@api_bp.route("/events/<int:eventid>", methods=["PATCH"])
def api_update_event(eventid):
    """PATCH update event."""
    data = request.json
    return update_event(eventid, data)


@api_bp.route("/events/<int:eventid>", methods=["DELETE"])
def api_delete_event(eventid):
    """DELETE event."""
    return delete_event(eventid)


# ========== Profile APIs ==========

@api_bp.route("/profiles", methods=["GET"])
def api_get_profiles():
    """GET all profiles."""
    return get_profiles()


@api_bp.route("/profiles/<int:profileid>", methods=["GET"])
def api_get_profile_by_id(profileid):
    """GET profile by ID."""
    return get_profile_by_id(profileid)


@api_bp.route("/profiles", methods=["POST"])
def api_create_profile():
    """POST create new profile."""
    data = request.json
    return create_profile(data)


@api_bp.route("/profiles/<int:profileid>", methods=["DELETE"])
def api_delete_profile(profileid):
    """DELETE profile."""
    return delete_profile(profileid)


# ========== EventXProfile APIs ==========

@api_bp.route("/eventxprofiles", methods=["GET"])
def api_get_eventxprofiles():
    """GET all eventxprofile associations."""
    return get_eventxprofiles()


@api_bp.route("/eventxprofiles/<int:eventxprofileid>", methods=["GET"])
def api_get_eventxprofile_by_id(eventxprofileid):
    """GET eventxprofile association by ID."""
    return get_eventxprofile_by_id(eventxprofileid)


@api_bp.route("/eventxprofiles", methods=["POST"])
def api_create_eventxprofile():
    """POST create new eventxprofile association."""
    data = request.json
    return create_eventxprofile(data)


@api_bp.route("/eventxprofiles/<int:eventxprofileid>", methods=["DELETE"])
def api_delete_eventxprofile(eventxprofileid):
    """DELETE eventxprofile association."""
    return delete_eventxprofile(eventxprofileid)
