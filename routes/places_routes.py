"""Places, suggestion settings, and turning a suggestion into an event."""

from datetime import datetime

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for,
)

from database.db_event import create_event, delete_event
from database.db_place import (
    create_place, delete_place, get_place_by_id, list_places, update_place,
)
from database.db_settings import (
    clean_preferences, get_preferences, preset_of, save_preferences,
)
from models.api_models.suggestion import Preferences
from models.db_models.place import CATEGORIES
from services.planner import account_plans
from utils.auth import is_safe_next
from utils.current_user import current_user_id
from utils.helpers import safe_int

places_bp = Blueprint("places", __name__)

# Visit lengths the form offers, in minutes
VISIT_CHOICES = [30, 60, 90, 120, 180, 240, 360]
ADDED = "added_event"   # session key for the "Added ... Undo" notice


def _error(response) -> str:
    return response[0].get_json().get("data", {}).get("error", "")


def _back(default_endpoint="web.homepage"):
    """Back to the page the form came from, if it is one of ours."""
    target = request.form.get("next")
    if is_safe_next(target):
        return redirect(target)
    return redirect(url_for(default_endpoint))


@places_bp.app_context_processor
def added_notice():
    """The notice after adding a suggestion, shown once on the next page."""
    return {"added_notice": session.pop(ADDED, None)}


# ---------- The places page ----------

@places_bp.route("/places")
def places_page():
    user_id = current_user_id()
    selected_id = safe_int(request.args.get("selected_placeid"), 0)
    selected = None
    if selected_id:
        response, status = get_place_by_id(selected_id, user_id)
        if status == 200:
            selected = response.get_json()["data"]
    plans = account_plans(user_id)
    try:
        places = list_places(user_id)
    except Exception:
        flash("Could not load your places. Please try again.", "error")
        places = []
    today_plan = plans.plan_for(plans.now.date())
    return render_template(
        "places.html",
        places=places,
        selected=selected,
        selected_id=selected_id,
        categories=CATEGORIES,
        visit_choices=VISIT_CHOICES,
        plans=plans,
        today_plan=today_plan,
    )


@places_bp.route("/places/load", methods=["POST"])
def load_place():
    placeid = safe_int(request.form.get("placeid"), 0)
    return redirect(url_for("places.places_page", selected_placeid=placeid))


@places_bp.route("/places/create", methods=["POST"])
def create_place_form():
    result = create_place(request.form, current_user_id())
    if result[1] == 201:
        flash(f"Added {result[0].get_json()['data']['name']} to your places.",
              "success")
        return redirect(url_for("places.places_page"))
    flash(_error(result) or "That place didn't save.", "error")
    return redirect(url_for("places.places_page"))


@places_bp.route("/places/update", methods=["POST"])
def update_place_form():
    placeid = safe_int(request.form.get("placeid"), 0)
    result = update_place(placeid, request.form, current_user_id())
    if result[1] == 200:
        flash("Your place is up to date.", "success")
        return redirect(url_for("places.places_page"))
    flash(_error(result) or "That change didn't save.", "error")
    return redirect(url_for("places.places_page", selected_placeid=placeid))


@places_bp.route("/places/delete", methods=["POST"])
def delete_place_form():
    placeid = safe_int(request.form.get("placeid"), 0)
    result = delete_place(placeid, current_user_id())
    if result[1] == 200:
        flash("Place deleted. Events you made from it are kept.", "success")
    else:
        flash(_error(result) or "That place couldn't be deleted.", "error")
    return redirect(url_for("places.places_page"))


# ---------- Settings ----------

@places_bp.route("/settings", methods=["GET", "POST"])
def settings_page():
    user_id = current_user_id()
    if request.method == "POST":
        try:
            prefs = clean_preferences(request.form)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("places.settings_page"))
        try:
            save_preferences(user_id, prefs)
        except Exception:
            flash("Your settings didn't save. Please try again.", "error")
            return redirect(url_for("places.settings_page"))
        flash("Your settings are saved.", "success")
        return redirect(url_for("places.settings_page"))

    try:
        prefs = get_preferences(user_id)
    except Exception:
        flash("Could not load your settings. Showing the defaults.", "error")
        prefs = Preferences()
    return render_template("settings.html", prefs=prefs,
                           preset=preset_of(prefs))


# ---------- From a suggestion to an event ----------

def _parse(value):
    try:
        return datetime.fromisoformat(value or "")
    except ValueError:
        return None


@places_bp.route("/suggestions/add", methods=["POST"])
def add_suggestion():
    """One click: the suggested visit becomes an event at the place."""
    user_id = current_user_id()
    placeid = safe_int(request.form.get("placeid"), 0)
    start, end = (_parse(request.form.get("start")),
                  _parse(request.form.get("end")))
    response, status = get_place_by_id(placeid, user_id)
    if status != 200 or not start or not end or end <= start:
        flash("That suggestion couldn't be added. Please try again.",
              "error")
        return _back()
    place = response.get_json()["data"]
    result = create_event({
        "name": place["name"],
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "location": place["address"] or place["name"],
        "place_id": place["id"],
    }, user_id)
    if result[1] != 201:
        flash(_error(result) or "That suggestion couldn't be added.",
              "error")
        return _back()
    event = result[0].get_json()["data"]
    session[ADDED] = {
        "id": event["id"],
        "name": place["name"],
        "text": (f"Added {place['name']}, "
                 f"{start:%a} {start.day} {start:%b} "
                 f"{start:%H:%M}-{end:%H:%M}."),
    }
    return _back()


@places_bp.route("/suggestions/undo", methods=["POST"])
def undo_suggestion():
    """Take back an event just added from a suggestion."""
    eventid = safe_int(request.form.get("eventid"), 0)
    result = delete_event(eventid, current_user_id())
    if result[1] == 200:
        name = (request.form.get("name") or "").strip()[:60] or "It"
        flash(f"Removed {name} from your calendar.", "success")
    else:
        flash("That event was already gone.", "error")
    return _back()
