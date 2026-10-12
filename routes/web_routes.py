"""Web routes blueprint for HTML pages and form handling."""

from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash

from database.db_event import (
    events_between,
    get_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
)
from database.db_place import get_place_by_id, list_places
from services.calendar_service import get_full_calendar
from services.datetime_service import get_today_detail
from services.planner import account_plans
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
    times are missing or malformed. The form sends a date and two times;
    a start sent as one date-and-time also works."""
    data = request.form.to_dict()
    if data.get("date"):
        data["start_time"] = f"{data['date']}T{data.get('start_time', '')}"
    try:
        times = parse_incoming_start_and_end_time(
            data.get("start_time", ""), data.get("end_time", "")
        )
    except (ValueError, AttributeError):
        return None
    data.update(times)
    return data


# ========== Routes ==========


def _chosen_day(value):
    """The ?day=YYYY-MM-DD the day panel is open for, if valid."""
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def _day_panel(user_id, day, plans):
    """What the day panel shows: the day's events, and its plan if the
    forecast reaches it."""
    start = datetime.combine(day, datetime.min.time())
    try:
        events = events_between(user_id, start, start + timedelta(days=1))
    except Exception:
        events = []
    today = plans.now.date()
    return {
        "day": day,
        "events": events,
        "plan": plans.plan_for(day),
        "past": day < today,
        "beyond": day > today and plans.plan_for(day) is None,
        "includes": plans.prefs.includes(day),
    }


@web_bp.route("/")
def homepage():
    """Homepage with today's weather and the month's calendar, plus the
    suggestions: today's at the top, the good days ahead, marks on good
    days in the month, and the panel for a chosen day."""
    user_id = current_user_id()
    today = get_today_detail()
    calendar_matrix = get_full_calendar(today["year"], today["month"])

    hourly_forecast = [r.to_dict() for r in get_hourly_forecast_today()]

    response, _ = get_events(user_id, today["year"], today["month"])
    monthly_event_data = _events_or_flash(response)

    plans = account_plans(user_id)
    chosen = _chosen_day(request.args.get("day"))
    great_days = {
        d.day for d in plans.great_days
        if (d.year, d.month) == (today["year"], today["month"])
    }

    return render_template(
        "index.html",
        calendar_matrix=calendar_matrix,
        today_detail=today,
        monthly_event_list=monthly_events_grouped(monthly_event_data),
        daily_event_list=build_daily_event_list(
            monthly_event_data, today["day"]
        ),
        hourly_forecast=hourly_forecast,
        plans=plans,
        great_days=great_days,
        panel=_day_panel(user_id, chosen, plans) if chosen else None,
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

    try:
        places = list_places(user_id)
    except Exception:
        places = []

    return render_template(
        "management.html",
        all_event=all_event,
        selected_event=selected_event,
        selected_eventid=selected_eventid,
        form=_event_form(user_id, selected_event),
        places=places,
    )


def _event_form(user_id, selected_event):
    """What the event form starts with: the chosen event; a suggestion
    (?place=&start=&end=, from "Add" on a suggestion); a day (?day=, from
    the day panel); or nothing."""
    if selected_event:
        start = selected_event["start_time"]   # "YYYY-MM-DDTHH:MM"
        return {
            "name": selected_event["name"],
            "date": start[:10], "start": start[11:16],
            "end": selected_event["end_time"],
            "location": selected_event["location"],
            "place_id": selected_event.get("place_id"),
        }

    placeid = safe_int(request.args.get("place"), 0)
    if placeid:
        response, status = get_place_by_id(placeid, user_id)
        try:
            start = datetime.fromisoformat(request.args.get("start", ""))
            end = datetime.fromisoformat(request.args.get("end", ""))
        except ValueError:
            start = end = None
        if status == 200 and start and end and start.date() == end.date():
            place = response.get_json()["data"]
            return {
                "name": place["name"][:60],
                "date": start.date().isoformat(),
                "start": f"{start:%H:%M}", "end": f"{end:%H:%M}",
                "location": place["address"] or place["name"],
                "place_id": place["id"],
                "from_suggestion": True,
            }

    chosen = _chosen_day(request.args.get("day"))
    return {
        "name": "", "location": "", "place_id": None,
        "date": chosen.isoformat() if chosen else "",
        "start": "09:00" if chosen else "", "end": "10:00" if chosen else "",
    }


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
