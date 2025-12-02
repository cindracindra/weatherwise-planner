from flask import Flask, render_template, request, redirect, url_for, jsonify

from api.event_api import (
    get_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
)
from api.profile_api import (
    get_profiles,
    get_profile_by_id,
    create_profile,
    delete_profile,
)

from api.event_profile_api import (
    get_event_profiles,
    get_event_by_profile,
    get_event_profile_by_id,
    create_event_profile,
    delete_event_profile,
)

from services.calendar_service import get_full_calendar
from services.datetime_service import get_today_detail
from services.event_services import (
    get_daily_event_by_profile,
    get_monthly_event_by_profile
)
from services.weather_service import get_hourly_forecast_today


app = Flask(__name__)


# ========== Routes ==========


# Route to homepage (index.html)
@app.route("/")
def homepage():
    username = request.args.get("username", "")
    profile_list = get_profiles()

    today = get_today_detail()

    # create appropriate function
    hourly_temp = get_hourly_forecast_today()

    if username:
        monthly_event_list = get_monthly_event_by_profile(username)
        daily_event_list = get_daily_event_by_profile(username)
    else:
        monthly_event_list = []
        daily_event_list = []

    return render_template(
        "index.html",
        calendar_matrix=get_full_calendar(today.year, today.month),
        today_detail=today,
        username=username,
        profile_list=profile_list["profiles"],
        monthly_event_list=monthly_event_list,
        daily_event_list=daily_event_list,
        hourly_temp=hourly_temp,
    )


@app.route("/profile", methods=['GET'])
def load_profile():
    username = request.args.get("username", "")
    return redirect(url_for("homepage", username=username))


@app.route("/reload_calendar", methods=['GET'])
def reload_calendar():
    username = request.args.get("username", "")
    return redirect(url_for("homepage", username=username))


# Route to management page
@app.route("/management")
def management():
    code = request.args.get("reqHttpCode", 100)
    if code == 100:
        username = request.args.get("username", "")
        selected_event_id = request.args.get("selected_event_id", "")

        # create appropriate function
        all_event = get_event_by_profile(username)
        selected_event = get_event(selected_event_id)

        return render_template(
            "event_management.html",
            username=username,
            all_event=all_event["event_by_profile"],
            selected_event=selected_event)

    elif code == 200 or code == 201:
        return render_template("management.html", isReqSucc=True)
    else:
        return render_template("management.html", isReqSucc=False)


# Route to trigger event creation from web
@app.route("/management/event/create", methods=["POST"])
def web_create_event():
    username = request.form.get("username", "")
    data = request.form
    result, status = create_event(data)
    return redirect(url_for("management", reqHttpCode=status))


# Route to trigger event update from web
@app.route("/management/event/update/<int:event_id>", methods=["POST"])
def web_update_event(event_id):
    data = request.form
    result, status = update_event(event_id, data)
    return redirect(url_for("management", reqHttpCode=status))


# Route to trigger event deletion from web
@app.route("/management/event/delete/<int:event_id>", methods=["POST"])
def web_delete_event(event_id):
    result, status = delete_event(event_id)
    return redirect(url_for("management", reqHttpCode=status))


# Route to trigger event-profile creation from web
@app.route("/management/event-profile/create", methods=["POST"])
def web_create_event_profile():
    data = request.form
    result, status = create_event_profile(data)
    return redirect(url_for("management", reqHttpCode=status))


# Route to trigger event-profile deletion from web
@app.route(
    "/management/event-profile/delete/<int:event_profile_id>",
    methods=["POST"],
)
def web_delete_event_profile(event_profile_id):
    result, status = delete_event_profile(event_profile_id)
    return redirect(url_for("management", reqHttpCode=status))


# Route to trigger profile creation from web
@app.route("/management/profile/create", methods=["POST"])
def web_create_profile():
    data = request.form
    result, status = create_profile(data)
    return redirect(url_for("management", reqHttpCode=status))


# Route to trigger profile deletion from web
@app.route("/management/profile/delete/<int:profile_id>", methods=["POST"])
def web_delete_profile(profile_id):
    result, status = delete_profile(profile_id)
    return redirect(url_for("management", reqHttpCode=status))


# ========== Event APIs ==========


# API: GET retrieve all events
@app.route("/api/events", methods=["GET"])
def api_get_events():
    return jsonify(get_events())


# API: GET retrieve event by id
@app.route("/api/events/<int:event_id>", methods=["GET"])
def api_get_event_by_id(event_id):
    result, status = get_event_by_id(event_id)
    return jsonify(result), status


# API: POST create event
@app.route("/api/events", methods=["POST"])
def api_create_event():
    data = request.json
    result, status = create_event(data)
    return jsonify(result), status


# API: PATCH update event
@app.route("/api/events/<int:event_id>", methods=["PATCH"])
def api_update_event(event_id):
    data = request.json
    result, status = update_event(event_id, data)
    return jsonify(result), status


# API: DELETE delete event
@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def api_delete_event(event_id):
    result, status = delete_event(event_id)
    return jsonify(result), status


# ========== Profile APIs ==========


# API: GET retrieve all profiles
@app.route("/api/profiles", methods=["GET"])
def api_get_profiles():
    return jsonify(get_profiles())


# API: GET retrieve profile by id
@app.route("/api/profiles/<int:profile_id>", methods=["GET"])
def api_get_profile_by_id(profile_id):
    result, status = get_profile_by_id(profile_id)
    return jsonify(result), status


# API: POST create profile
@app.route("/api/profiles", methods=["POST"])
def api_create_profile():
    data = request.json
    result, status = create_profile(data)
    return jsonify(result), status


# API: DELETE delete profile
@app.route("/api/profiles/<int:profile_id>", methods=["DELETE"])
def api_delete_profile(profile_id):
    result, status = delete_profile(profile_id)
    return jsonify(result), status


# ========== Event-Profile APIs ==========


# API: GET retrieve all event-profiles
@app.route("/api/event-profiles", methods=["GET"])
def api_get_event_profiles():
    return jsonify(get_event_profiles())


# API: GET retrieve event-profile by id
@app.route("/api/event-profiles/<int:event_profile_id>", methods=["GET"])
def api_get_event_profile_by_id(event_profile_id):
    result, status = get_event_profile_by_id(event_profile_id)
    return jsonify(result), status


# API: POST create event-profile
@app.route("/api/event-profiles", methods=["POST"])
def api_create_event_profile():
    data = request.json
    result, status = create_event_profile(data)
    return jsonify(result), status


# API: DELETE delete event-profile
@app.route("/api/event-profiles/<int:event_profile_id>", methods=["DELETE"])
def api_delete_event_profile(event_profile_id):
    result, status = delete_event_profile(event_profile_id)
    return jsonify(result), status
