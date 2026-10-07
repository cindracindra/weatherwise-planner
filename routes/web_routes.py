"""Web routes blueprint for HTML pages and form handling."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from database.db_event import (
    get_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
)
from services.calendar_service import get_full_calendar
from services.datetime_service import get_today_detail
from services.weather_service import get_hourly_forecast_today
from utils.current_user import current_user_id
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


def _events_or_flash(response):
    """The events payload, or an empty one with an error message shown."""
    payload = response.get_json()
    if payload.get("statusCode") != 200:
        error = payload.get("data", {}).get("error", "Unknown error")
        flash(f"Could not load events: {error}", "error")
        return {"events": []}
    return payload["data"]


def _form_with_times():
    """The posted form with start/end parsed into datetimes, or None if the
    times are missing or malformed."""
    data = request.form.to_dict()
    try:
        times = parse_incoming_start_and_end_time(
            data.get("start_time", ""), data.get("end_time", "")
        )
    except (ValueError, AttributeError):
        return None
    data.update(times)
    return data


# ========== Routes ==========


@web_bp.route("/")
def homepage():
    """Homepage with today's weather and the month's calendar."""
    user_id = current_user_id()
    today = get_today_detail()
    calendar_matrix = get_full_calendar(today["year"], today["month"])

    hourly_forecast = [r.to_dict() for r in get_hourly_forecast_today()]

    response, _ = get_events(user_id, today["year"], today["month"])
    monthly_event_data = _events_or_flash(response)

    return render_template(
        "index.html",
        calendar_matrix=calendar_matrix,
        today_detail=today,
        monthly_event_list=monthly_events_grouped(monthly_event_data),
        daily_event_list=build_daily_event_list(monthly_event_data),
        hourly_forecast=hourly_forecast,
    )


@web_bp.route("/reload", methods=["GET"])
def reload_calendar():
    """Reload calendar page."""
    return redirect(url_for("web.homepage"))


@web_bp.route("/management/event")
def web_management():
    """Event management page."""
    user_id = current_user_id()
    code = safe_int(request.args.get("reqHttpCode"), 100)
    selected_eventid = safe_int(request.args.get("selected_eventid"), 0)

    response, _ = get_events(user_id)
    all_event = group_all_events_by_full_date(_events_or_flash(response))

    selected_event = None
    if selected_eventid:
        response, _ = get_event_by_id(selected_eventid, user_id)
        payload = response.get_json()
        if payload.get("statusCode") == 200:
            selected_event = parse_event_for_datepicker(payload["data"])

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
        all_event=all_event,
        selected_event=selected_event,
        selected_eventid=selected_eventid,
    )


@web_bp.route("/management/event/load", methods=["POST"])
def web_load_event():
    """Load event for editing."""
    eventid = safe_int(request.form.get("eventid", ""))
    return redirect(url_for("web.web_management", selected_eventid=eventid))


@web_bp.route("/management/event/create", methods=["POST"])
def web_create_event():
    """Create new event from web form."""
    data = _form_with_times()
    if data is None:
        return redirect(url_for("web.web_management", reqHttpCode=400))
    _, status = create_event(data, current_user_id())
    return redirect(url_for("web.web_management", reqHttpCode=status))


@web_bp.route("/management/event/update", methods=["POST"])
def web_update_event():
    """Update existing event from web form."""
    eventid = safe_int(request.form.get("eventid", ""))
    data = _form_with_times()
    if data is None:
        return redirect(url_for("web.web_management", reqHttpCode=400))
    _, status = update_event(eventid, data, current_user_id())
    return redirect(url_for("web.web_management", reqHttpCode=status))


@web_bp.route("/management/event/delete", methods=["POST"])
def web_delete_event():
    """Delete event from web form."""
    eventid = safe_int(request.form.get("eventid", ""))
    _, status = delete_event(eventid, current_user_id())
    return redirect(url_for("web.web_management", reqHttpCode=status))
