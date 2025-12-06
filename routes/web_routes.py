"""Web routes blueprint for HTML pages and form handling."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from database.db_profile import get_profiles, create_profile, delete_profile
from database.db_event import get_event_by_id, update_event
from database.db_composite import (
    get_events_by_profile_id,
    get_events_by_profile_id_by_month,
    create_event_and_profile_association,
    delete_event_and_profile_association
)
from services.calendar_service import get_full_calendar
from services.datetime_service import get_today_detail
from services.weather_service import get_hourly_forecast_today
from utils.datafeed import (
    build_daily_event_list,
    monthly_events_grouped,
    group_all_events_by_full_date,
    parse_event_for_datepicker
)
from utils.helpers import safe_int

# Create blueprint
web_bp = Blueprint('web', __name__)


# ========== Routes ==========

@web_bp.route("/")
def homepage():
    """Homepage with calendar view."""
    isReqSucc = request.args.get("isReqSucc", "True")
    if isReqSucc == "False":
        flash('Select a profile to manage events.', 'error')

    profile_id = request.args.get("profile_id", "")
    profile_response, _ = get_profiles()
    profile_data = profile_response.get_json()["data"]

    today = get_today_detail()
    calendar_matrix = get_full_calendar(today["year"], today["month"])

    hourly_forecast = get_hourly_forecast_today()
    hourly_forecast = [reading.to_dict() for reading in hourly_forecast]

    if profile_id:
        monthly_event_response, _ = get_events_by_profile_id_by_month(
            profile_id, today["year"], today["month"]
        )
        monthly_event_data = monthly_event_response.get_json()["data"]
        daily_event_list = build_daily_event_list(monthly_event_data)
        monthly_event_list = monthly_events_grouped(monthly_event_data)
    else:
        monthly_event_data = {}
        daily_event_list = []
        monthly_event_list = []

    return render_template(
        "index.html",
        calendar_matrix=calendar_matrix,
        today_detail=today,
        profile_id=profile_id,
        profile_list=profile_data["profiles"],
        monthly_event_list=monthly_event_list,
        daily_event_list=daily_event_list,
        hourly_forecast=hourly_forecast,
    )


@web_bp.route("/reload", methods=['GET'])
def reload_calendar():
    """Reload calendar page."""
    profile_id = request.args.get("profile_id", "")
    return redirect(url_for("web.homepage", profile_id=profile_id))


@web_bp.route("/management", methods=['GET'])
def management_handle_form():
    """Handle management form submission."""
    profile_id = request.args.get("profile_id", "")

    if not profile_id:
        return redirect(url_for("web.homepage", isReqSucc=False))
    else:
        return redirect(url_for("web.web_management", profile_id=profile_id))


@web_bp.route("/management/event")
def web_management():
    """Event management page."""
    profile_id = request.args.get("profile_id", "")
    code = safe_int(request.args.get("reqHttpCode"), 100)
    selected_event_id = safe_int(request.args.get("selected_event_id"), 0)

    all_event = []
    selected_event = None

    if profile_id:
        event_response, _ = get_events_by_profile_id(profile_id)
        event_data = event_response.get_json()["data"]
        all_event = group_all_events_by_full_date(event_data)

        if selected_event_id:
            event_response, _ = get_event_by_id(selected_event_id)
            response_json = event_response.get_json()
            event = response_json["data"]
            if event and not event.get("error"):
                selected_event = parse_event_for_datepicker(event)

        # Handle flash messages
        if code in [200, 201]:
            flash('Event successfully updated/created/deleted', 'success')
        elif code != 100:
            flash('Unable to update/create/delete event', 'error')

        return render_template(
            "management.html",
            profile_id=profile_id,
            all_event=all_event,
            selected_event=selected_event,
            selected_event_id=selected_event_id
        )


@web_bp.route("/management/event/load", methods=["POST"])
def web_load_event():
    """Load event for editing."""
    profile_id = request.form.get("profile_id", "")
    event_id = safe_int(request.form.get("event_id", ""))
    return redirect(url_for(
        "web.web_management",
        profile_id=profile_id,
        selected_event_id=event_id))


@web_bp.route("/management/event/create", methods=["POST"])
def web_create_event():
    """Create new event from web form."""
    profile_id = request.form.get("profile_id", "")
    data = request.form
    result, status = create_event_and_profile_association(
        data['name'],
        data['start_time'],
        data['end_time'],
        data['location'],
        profile_id
    )
    return redirect(url_for(
        "web.web_management",
        reqHttpCode=status,
        profile_id=profile_id))


@web_bp.route("/management/event/update", methods=["POST"])
def web_update_event():
    """Update existing event from web form."""
    profile_id = request.form.get("profile_id", "")
    event_id = safe_int(request.form.get("event_id", ""))
    data = request.form
    result, status = update_event(event_id, data)
    return redirect(url_for(
        "web.web_management",
        reqHttpCode=status,
        profile_id=profile_id))


@web_bp.route("/management/event/delete", methods=["POST"])
def web_delete_event():
    """Delete event from web form."""
    profile_id = request.form.get("profile_id", "")
    event_id = safe_int(request.form.get("event_id", ""))
    result, status = delete_event_and_profile_association(event_id)
    return redirect(url_for(
        "web.web_management",
        reqHttpCode=status,
        profile_id=profile_id))


@web_bp.route("/management/profile")
def web_profile():
    """Profile management page."""
    code = safe_int(request.args.get("reqHttpCode"), 100)
    profile_response, _ = get_profiles()
    profile_data = profile_response.get_json()["data"]

    if code in [200, 201]:
        flash('Profile successfully created/deleted', 'success')
    elif code != 100:
        flash('Unable to create/delete profile', 'error')

    return render_template(
        "management_profile.html",
        profile_list=profile_data["profiles"])


@web_bp.route("/management/profile/create", methods=["POST"])
def web_create_profile():
    """Create new profile from web form."""
    data = request.form
    result, status = create_profile(data)
    return redirect(url_for("web.web_profile", reqHttpCode=status))


@web_bp.route("/management/profile/delete", methods=["POST"])
def web_delete_profile():
    """Delete profile from web form."""
    profile_id = request.form.get("profile_id", "")
    result, status = delete_profile(profile_id)
    return redirect(url_for("web.web_profile", reqHttpCode=status))
