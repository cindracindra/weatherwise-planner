from flask import Flask, render_template, request, redirect, url_for, jsonify

# TODO: created edit_event function
from api.event_api import get_events, create_event, delete_event
from api.profile_api import get_profiles, create_profile, delete_profile
from api.event_profile_api import (
    get_event_profiles,
    create_event_profile,
    delete_event_profile,
)

from my_calendar import get_month_calendar_matrix_weather
from weather import get_hourly_weather

import calendar
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def homepage():
    username = request.args.get("username", "")
    profile_list = get_profiles()

    now = datetime.now()
    today_detail = {
        "day": calendar.day_name[now.weekday()],
        "date": now.day,
        "month": calendar.month_name[now.month],
        "year": now.year
    }
    
    hourly_temp = get_hourly_temp() # create appropriate function
    
    if username:
        event_list = get_events_for_user(username) # create appropriate function
    else:
        event_list = []

    return render_template(
        "index.html",
        calendar_matrix=get_month_calendar_matrix_weather(today_detail['year'], now.month),
        today_detail=today_detail,
        username=username,
        profile_list=profile_list["profiles"],
        event_list=event_list,
        hourly_temp=hourly_temp,
    )

@app.route("/profile", methods=['GET'])
def load_profile():
    username = request.args.get("username", "")
    return redirect(url_for("homepage", username=username))

@app.route("/reload_calendar", methods=['GET']) 
def reload_calendar():
    username = request.args.get("username", "")
    return redirect(url_for("homepage",username=username))

@app.route("/management")
def management():
    username = request.args.get("username", "")
    selected_event_id = request.args.get("selected_event_id", "")
    
    all_event = get_events_for_user(username) # create appropriate function
    selected_event = get_selected_event(selected_event_id) # create appropriate function
    
    return render_template(
        "event_management.html", 
        username=username,
        all_event=all_event,
        selected_event=selected_event) 

@app.route("/management/load-event/<int:event_id>", methods=["POST"])
def web_load_event(event_id):
    username = request.form.get("username", "")
    return redirect(url_for("management", username=username, selected_event_id=event_id))

@app.route("/management/edit-event/<int:event_id>", methods=["POST"])
def web_edit_event(event_id):
    username = request.form.get("username", "")
    data = request.form
    return redirect(url_for("management", username=username))


@app.route("/management/create-event", methods=["POST"])
def web_create_event():
    username = request.form.get("username", "")
    data = request.form
    return redirect(url_for("management", username=username))


@app.route("/management/create-event-profile", methods=["POST"])
def web_create_event_profile():
    data = request.form
    create_event_profile(data)
    return redirect(url_for("management"))


@app.route("/management/create-profile", methods=["POST"])
def web_create_profile():
    data = request.form
    create_profile(data)
    return redirect(url_for("management"))


# Web route: Delete event (form/button)
@app.route("/management/delete-event/<int:event_id>", methods=["POST"])
def web_delete_event(event_id):
    delete_event(event_id)
    return redirect(url_for("management"))


# Web route: Delete event profile (form/button)
@app.route(
    "/management/delete-event-profile/<int:event_profile_id>",
    methods=["POST"],
)
def web_delete_event_profile(event_profile_id):
    delete_event_profile(event_profile_id)
    return redirect(url_for("management"))


# Web route: Delete profile (form/button)
@app.route("/management/delete-profile/<int:profile_id>", methods=["POST"])
def web_delete_profile(profile_id):
    delete_profile(profile_id)
    return redirect(url_for("management"))


@app.route("/api/events", methods=["GET"])
def api_get_events():
    return get_events()


@app.route("/api/events", methods=["POST"])
def api_create_event():
    data = request.json
    return create_event(data)


@app.route("/api/profiles", methods=["GET"])
def api_get_profiles():
    return get_profiles()


@app.route("/api/profiles", methods=["POST"])
def api_create_profile():
    data = request.json
    return create_profile(data)


@app.route("/api/profiles/<int:profile_id>", methods=["DELETE"])
def api_delete_profile(profile_id):
    result, status = delete_profile(profile_id)
    return jsonify(result), status


@app.route("/api/event-profiles", methods=["GET"])
def api_get_event_profiles():
    return get_event_profiles()


@app.route("/api/event-profiles", methods=["POST"])
def api_create_event_profile():
    data = request.json
    return create_event_profile(data)


# API route: Delete event
@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def api_delete_event(event_id):
    result, status = delete_event(event_id)
    return jsonify(result), status


# API route: Delete event profile
@app.route("/api/event-profiles/<int:event_profile_id>", methods=["DELETE"])
def api_delete_event_profile(event_profile_id):
    result, status = delete_event_profile(event_profile_id)
    return jsonify(result), status
