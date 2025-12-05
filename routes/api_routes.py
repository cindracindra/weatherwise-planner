"""API routes blueprint for REST API endpoints."""

from flask import Blueprint, request, jsonify

from database.event import (
    get_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
)
from database.profile import (
    get_profiles,
    get_profile_by_id,
    create_profile,
    delete_profile,
)
from database.eventxprofile import (
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
    return jsonify(get_events())


@api_bp.route("/events/<int:event_id>", methods=["GET"])
def api_get_event_by_id(event_id):
    """GET event by ID."""
    result, status = get_event_by_id(event_id)
    return jsonify(result), status


@api_bp.route("/events", methods=["POST"])
def api_create_event():
    """POST create new event."""
    data = request.json
    result, status = create_event(data)
    return jsonify(result), status


@api_bp.route("/events/<int:event_id>", methods=["PATCH"])
def api_update_event(event_id):
    """PATCH update event."""
    data = request.json
    result, status = update_event(event_id, data)
    return jsonify(result), status


@api_bp.route("/events/<int:event_id>", methods=["DELETE"])
def api_delete_event(event_id):
    """DELETE event."""
    result, status = delete_event(event_id)
    return jsonify(result), status


# ========== Profile APIs ==========

@api_bp.route("/profiles", methods=["GET"])
def api_get_profiles():
    """GET all profiles."""
    return jsonify(get_profiles())


@api_bp.route("/profiles/<int:profile_id>", methods=["GET"])
def api_get_profile_by_id(profile_id):
    """GET profile by ID."""
    result, status = get_profile_by_id(profile_id)
    return jsonify(result), status


@api_bp.route("/profiles", methods=["POST"])
def api_create_profile():
    """POST create new profile."""
    data = request.json
    result, status = create_profile(data)
    return jsonify(result), status


@api_bp.route("/profiles/<int:profile_id>", methods=["DELETE"])
def api_delete_profile(profile_id):
    """DELETE profile."""
    result, status = delete_profile(profile_id)
    return jsonify(result), status


# ========== Event-Profile APIs ==========

@api_bp.route("/event-profiles", methods=["GET"])
def api_get_event_profiles():
    """GET all event-profile associations."""
    return jsonify(get_eventxprofiles())


@api_bp.route("/event-profiles/<int:event_profile_id>", methods=["GET"])
def api_get_event_profile_by_id(event_profile_id):
    """GET event-profile association by ID."""
    result, status = get_eventxprofile_by_id(event_profile_id)
    return jsonify(result), status


@api_bp.route("/event-profiles", methods=["POST"])
def api_create_event_profile():
    """POST create new event-profile association."""
    data = request.json
    result, status = create_eventxprofile(data)
    return jsonify(result), status


@api_bp.route("/event-profiles/<int:event_profile_id>", methods=["DELETE"])
def api_delete_event_profile(event_profile_id):
    """DELETE event-profile association."""
    result, status = delete_eventxprofile(event_profile_id)
    return jsonify(result), status
