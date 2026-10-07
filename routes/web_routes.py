"""Web routes blueprint for HTML pages and form handling."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from database.db_profile import get_profiles, create_profile, delete_profile
from database.db_event import get_event_by_id, update_event
from database.db_composite import (
    get_events_by_profileid,
    get_events_by_profileid_by_month,
    create_event_and_profile_association,
    delete_event_and_profile_association,
)
from services.calendar_service import get_full_calendar
from services.datetime_service import get_today_detail
from services.weather_service import get_hourly_forecast_today
from utils.datafeed import (
    build_daily_event_list,
    monthly_events_grouped,
    group_all_events_by_full_date,
    parse_event_for_datepicker,
    parse_incoming_start_and_end_time,
)
from utils.helpers import safe_int

# Create blueprint
web_bp = Blueprint("web", __name__)


# ========== Routes ==========


@web_bp.route("/")
def homepage():
    """Homepage with calendar view."""
    isReqSucc = request.args.get("isReqSucc", "True")
    if isReqSucc == "False":
        flash("Choose a profile first, then add your events.", "error")

    profileid = request.args.get("profileid", "")
    profile_response, status_code = get_profiles()
    profile_json = profile_response.get_json()

    # Handle database errors gracefully
    if profile_json.get("statusCode") != 200:
        flash(
            f'Database error: {
                profile_json.get("data", {}).get("error", "Unknown error")}',
            "error",
        )
        profile_list = []
    else:
        profile_list = profile_json["data"].get("profiles", [])

    today = get_today_detail()
    calendar_matrix = get_full_calendar(today["year"], today["month"])

    hourly_forecast = get_hourly_forecast_today()
    hourly_forecast = [reading.to_dict() for reading in hourly_forecast]

    if profileid:
        monthly_event_response, _ = get_events_by_profileid_by_month(
            profileid, today["year"], today["month"]
        )
        monthly_event_json = monthly_event_response.get_json()

        # Handle database errors gracefully
        if monthly_event_json.get("statusCode") != 200:
            flash(
                f'Could not load events: {
                    monthly_event_json.get(
                        "data", {}).get("error", "Unknown error")}',
                "error",
            )
            monthly_event_list = []
            daily_event_list = []
        else:
            monthly_event_data = monthly_event_json["data"]
            daily_event_list = build_daily_event_list(monthly_event_data)
            monthly_event_list = monthly_events_grouped(monthly_event_data)
    else:
        monthly_event_list = []
        daily_event_list = []

    return render_template(
        "index.html",
        calendar_matrix=calendar_matrix,
        today_detail=today,
        profileid=profileid,
        profile_list=profile_list,
        monthly_event_list=monthly_event_list,
        daily_event_list=daily_event_list,
        hourly_forecast=hourly_forecast,
    )


@web_bp.route("/reload", methods=["GET"])
def reload_calendar():
    """Reload calendar page."""
    profileid = request.args.get("profileid", "")
    return redirect(url_for("web.homepage", profileid=profileid))


@web_bp.route("/management", methods=["GET"])
def management_handle_form():
    """Handle management form submission."""
    profileid = request.args.get("profileid", "")

    if not profileid:
        return redirect(url_for("web.homepage", isReqSucc=False))
    else:
        return redirect(url_for("web.web_management", profileid=profileid))


@web_bp.route("/management/event")
def web_management():
    """Event management page."""
    profileid = request.args.get("profileid", "")
    code = safe_int(request.args.get("reqHttpCode"), 100)
    selected_eventid = safe_int(request.args.get("selected_eventid"), 0)

    all_event = []
    selected_event = None

    if profileid:
        event_response, _ = get_events_by_profileid(profileid)
        event_json = event_response.get_json()

        # Handle database errors gracefully
        if event_json.get("statusCode") != 200:
            flash(
                f'Could not load events: {
                    event_json.get("data", {}).get("error", "Unknown error")}',
                "error",
            )
            all_event = []
        else:
            event_data = event_json["data"]
            all_event = group_all_events_by_full_date(event_data)

        if selected_eventid:
            event_response, status_code = get_event_by_id(selected_eventid)
            response_json = event_response.get_json()
            # Check if the response was successful (statusCode 200)
            if response_json.get("statusCode") == 200:
                event = response_json["data"]
                selected_event = parse_event_for_datepicker(event)

        # Handle flash messages
        if code in [200, 201]:
            flash("Your events are up to date.", "success")
        elif code != 100:
            flash(
                "That change didn't save. Check the end time is after the "
                "start time and try again.",
                "error",
            )

        return render_template(
            "management.html",
            profileid=profileid,
            all_event=all_event,
            selected_event=selected_event,
            selected_eventid=selected_eventid,
        )


@web_bp.route("/management/event/load", methods=["POST"])
def web_load_event():
    """Load event for editing."""
    profileid = request.form.get("profileid", "")
    eventid = safe_int(request.form.get("eventid", ""))
    return redirect(
        url_for(
            "web.web_management",
            profileid=profileid,
            selected_eventid=eventid,
        )
    )


@web_bp.route("/management/event/create", methods=["POST"])
def web_create_event():
    """Create new event from web form."""
    profileid = request.form.get("profileid", "")
    data = request.form

    time_data = parse_incoming_start_and_end_time(
        data["start_time"],
        data["end_time"]
    )

    result, status = create_event_and_profile_association(
        data["name"],
        time_data["start_time"],
        time_data["end_time"],
        data["location"],
        profileid,
    )
    return redirect(
        url_for(
            "web.web_management", reqHttpCode=status, profileid=profileid
        )
    )


@web_bp.route("/management/event/update", methods=["POST"])
def web_update_event():
    """Update existing event from web form."""
    profileid = request.form.get("profileid", "")
    eventid = safe_int(request.form.get("eventid", ""))
    data = request.form.to_dict()

    time_data = parse_incoming_start_and_end_time(
        data["start_time"],
        data["end_time"]
    )

    data["start_time"] = time_data["start_time"]
    data["end_time"] = time_data["end_time"]

    result, status = update_event(eventid, data)
    return redirect(
        url_for(
            "web.web_management", reqHttpCode=status, profileid=profileid
        )
    )


@web_bp.route("/management/event/delete", methods=["POST"])
def web_delete_event():
    """Delete event from web form."""
    profileid = request.form.get("profileid", "")
    eventid = safe_int(request.form.get("eventid", ""))
    result, status = delete_event_and_profile_association(eventid)
    return redirect(
        url_for(
            "web.web_management", reqHttpCode=status, profileid=profileid
        )
    )


@web_bp.route("/management/profile")
def web_profile():
    """Profile management page."""
    code = safe_int(request.args.get("reqHttpCode"), 100)
    profile_response, _ = get_profiles()
    profile_json = profile_response.get_json()

    # Handle database errors gracefully
    if profile_json.get("statusCode") != 200:
        flash(
            f'Database error: {
                profile_json.get("data", {}).get("error", "Unknown error")}',
            "error",
        )
        profile_list = []
    else:
        profile_list = profile_json["data"].get("profiles", [])

    if code in [200, 201]:
        flash("Your profiles are up to date.", "success")
    elif code != 100:
        flash("That change didn't save. Try again.", "error")

    return render_template(
        "management_profile.html",
        profile_list=profile_list,
        profileid=request.args.get("profileid", ""),
    )


@web_bp.route("/management/profile/create", methods=["POST"])
def web_create_profile():
    """Create new profile from web form."""
    data = request.form
    result, status = create_profile(data)
    return redirect(url_for("web.web_profile", reqHttpCode=status))


@web_bp.route("/management/profile/delete", methods=["POST"])
def web_delete_profile():
    """Delete profile from web form."""
    profileid = request.form.get("profileid", "")
    result, status = delete_profile(profileid)
    return redirect(url_for("web.web_profile", reqHttpCode=status))
