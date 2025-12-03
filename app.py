from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

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
    get_event_profile_by_id,
    create_event_profile,
    delete_event_profile,
)

# from api.composite_api import get_events_by_profile_id

from services.calendar_service import get_full_calendar
from services.datetime_service import get_today_detail
from services.event_services import (
    dummy_get_daily_event_by_profile,
    dummy_get_monthly_event_by_profile,
    dummy_get_all_event_by_profile,
    dummy_get_event_by_id
)
from services.weather_service import get_hourly_forecast_today
from services.profile_service import dummy_get_profiles

app = Flask(__name__)
app.secret_key = 'event-calendar'

# ========== Routes ==========


# Route to homepage (index.html)
@app.route("/")
def homepage():
    isReqSucc = request.args.get("isReqSucc", True)
    if isReqSucc == "False":
        flash('Select a profile to manage events.', 'error')
    
    profile_id = request.args.get("profile_id", "")
    profile_list = dummy_get_profiles()

    today = get_today_detail()
    calendar_matrix = get_full_calendar(today["year"], today["month"])

    hourly_forecast = get_hourly_forecast_today()
    hourly_forecast = [reading.to_dict() for reading in hourly_forecast]

    if profile_id:
        monthly_event_list = dummy_get_monthly_event_by_profile(profile_id)
        daily_event_list = dummy_get_daily_event_by_profile(profile_id)
    else:
        monthly_event_list = []
        daily_event_list = []

    return render_template(
        "index.html",
        calendar_matrix=calendar_matrix,
        today_detail=today,
        profile_id=profile_id,
        profile_list=profile_list["profiles"],
        monthly_event_list=monthly_event_list,
        daily_event_list=daily_event_list,
        hourly_forecast=hourly_forecast,
    )


@app.route("/reload", methods=['GET'])
def reload_calendar():
    profile_id = request.args.get("profile_id", "")
    return redirect(url_for("homepage", profile_id=profile_id))


@app.route("/management", methods=['GET'])
def management_handle_form():
    profile_id = request.args.get("profile_id", "")
    
    if not profile_id:
        return redirect(url_for("homepage", isReqSucc=False))
    else:
        return redirect(url_for(
            "web_management",
            profile_id=profile_id))


# Route to management page
@app.route("/management/event")
def web_management():
    profile_id = request.args.get("profile_id", "")
    code = request.args.get("reqHttpCode", 100)
    selected_event_id = int(request.args.get("selected_event_id", 0))
        
    # create appropriate function
    all_event = dummy_get_all_event_by_profile(profile_id)
    selected_event = dummy_get_event_by_id(selected_event_id)
    
    if code == 100:
        return render_template(
            "management.html",
            profile_id=profile_id,
            all_event=all_event,
            selected_event=selected_event)

    elif code == 200 or code == 201:
        flash('Event successfully updated/created/deleted', 'success')
        return render_template(
            "management.html", 
            profile_id=profile_id,
            all_event=all_event,
            selected_event=selected_event)
    else:
        flash('Unable to update/create/delete event', 'error')
        return render_template(
            "management.html",
            profile_id=profile_id,
            all_event=all_event,
            selected_event=selected_event)


@app.route("/management/event/load/<int:event_id>", methods=["POST"])
def web_load_event(event_id):
    profile_id = request.form.get("profile_id", "")
    return redirect(url_for(
        "web_management",
        profile_id=profile_id,
        selected_event_id=event_id))


# Route to trigger event creation from web
@app.route("/management/event/create", methods=["POST"])
def web_create_event():
    profile_id = request.form.get("profile_id", "")
    data = request.form
    result, status = create_event(data)
    return redirect(url_for(
        "web_management",
        reqHttpCode=status,
        profile_id=profile_id))


# Route to trigger event update from web
@app.route("/management/event/update/<int:event_id>", methods=["POST"])
def web_update_event(event_id):
    profile_id = request.form.get("profile_id", "")
    data = request.form
    result, status = update_event(event_id, data)
    return redirect(url_for(
        "web_management",
        reqHttpCode=status,
        profile_id=profile_id))


# Route to trigger event deletion from web
@app.route("/management/event/delete/<int:event_id>", methods=["POST"])
def web_delete_event(event_id):
    profile_id = request.form.get("profile_id", "")
    result, status = delete_event(event_id)
    return redirect(url_for(
        "web_management",
        reqHttpCode=status,
        profile_id=profile_id))


# # Route to trigger event-profile creation from web
# @app.route("/management/event-profile/create", methods=["POST"])
# def web_create_event_profile():
#     data = request.form
#     result, status = create_event_profile(data)
#     return redirect(url_for("management/event", reqHttpCode=status))


# # Route to trigger event-profile deletion from web
# @app.route(
#     "/management/event-profile/delete/<int:event_profile_id>",
#     methods=["POST"],
# )
# def web_delete_event_profile(event_profile_id):
#     result, status = delete_event_profile(event_profile_id)
#     return redirect(url_for("management/event", reqHttpCode=status))


@app.route("/management/profile")
def web_profile():
    code = request.args.get("reqHttpCode", 100)
    profile_list = dummy_get_profiles()
    
    if code == 100:
        return render_template(
            "management_profile.html",
            profile_list=profile_list["profiles"])
    elif code == 200 or code == 201:
        flash('Profile successfully created/ deleted', 'success')
        return render_template(
            "management_profile.html",
            profile_list=profile_list["profiles"])
    else:
        flash('Unable to create/delete profile', 'error')
        return render_template(
            "management_profile.html",
            profile_list=profile_list["profiles"])


# Route to trigger profile creation from web
@app.route("/management/profile/create", methods=["POST"])
def web_create_profile():
    data = request.form
    result, status = create_profile(data)
    return redirect(url_for("web_profile", reqHttpCode=status))


# Route to trigger profile deletion from web
@app.route("/management/profile/delete", methods=["POST"])
def web_delete_profile():
    profile_id = request.form.get("profile_id", "")
    result, status = delete_profile(profile_id)
    return redirect(url_for("web_profile", reqHttpCode=status))


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
