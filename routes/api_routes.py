"""API routes blueprint for REST API endpoints.

Every endpoint works on the current account's events and places only.
"""

from flask import Blueprint, request

from database.db_event import (
    get_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
)
from database.db_place import (
    create_place,
    delete_place,
    get_place_by_id,
    get_places,
    update_place,
)
from services.planner import account_plans
from utils.current_user import current_user_id
from utils.response import StatusCode, build_response

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


# ========== Place APIs ==========

@api_bp.route("/places", methods=["GET"])
def api_get_places():
    """GET the account's places."""
    return get_places(current_user_id())


@api_bp.route("/places/<int:placeid>", methods=["GET"])
def api_get_place_by_id(placeid):
    """GET one of the account's places."""
    return get_place_by_id(placeid, current_user_id())


@api_bp.route("/places", methods=["POST"])
def api_create_place():
    """POST create a new place."""
    return create_place(request.get_json(silent=True), current_user_id())


@api_bp.route("/places/<int:placeid>", methods=["PATCH"])
def api_update_place(placeid):
    """PATCH update one of the account's places."""
    return update_place(placeid, request.get_json(silent=True),
                        current_user_id())


@api_bp.route("/places/<int:placeid>", methods=["DELETE"])
def api_delete_place(placeid):
    """DELETE one of the account's places (its events are kept)."""
    return delete_place(placeid, current_user_id())


# ========== Suggestions ==========

def _suggestion(s):
    return {
        "place_id": s.place.id,
        "place": s.place.name,
        "fit": s.fit,
        "fit_label": s.fit_label,
        "weather": s.kind_label,
        "start_time": s.start.isoformat(),
        "end_time": s.end.isoformat(),
        "temperature": s.temperature,
        "reasons": s.reasons,
    }


@api_bp.route("/suggestions", methods=["GET"])
def api_get_suggestions():
    """GET every forecast day with how each of the account's places fits
    it, best first, and whether the day is one the account asked for."""
    plans = account_plans(current_user_id())
    days = []
    for plan in plans.plans:
        o = plan.outlook
        days.append({
            "date": plan.day.isoformat(),
            "weather": plan.kind,
            "high": o.high,
            "low": o.low,
            "rain_chance": o.rain_chance,
            "in_your_days": plans.prefs.includes(plan.day),
            "busy": plan.busy,
            "picks": [s.place.id for s in plan.picks],
            "places": [_suggestion(s) for s in plan.suggestions],
        })
    return build_response(StatusCode.OK, {"days": days})
