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
import calendar
from datetime import date, datetime

app = Flask(__name__)

current_day_event = [
    {"id": 1, "name": "Meeting", "start": "10", "end": "11", "duration": 1},
    {"id": 2, "name": "Workout", "start": "18", "end": "18.5", "duration": 0.5},
    {"id": 3, "name": "Test", "start": "18.5", "end": "19", "duration": 0.5}
    ]

current_month_event = [
    {"date": 27, "day": "Thursday, 27 November 2025", "daily_events": current_day_event},
    {"date": 30, "day": "Sunday, 30 November 2025", "daily_events": current_day_event}
]

all_event = [
    {"date": 27, "day": "Thursday, 27 November 2025", "daily_events": current_day_event},
    {"date": 30, "day": "Sunday, 30 November 2025", "daily_events": current_day_event}
]

hourly_temp = [
    { "hour_number": 12, "hour_ampm": "AM", "temperature": 5 },
    { "hour_number": 1, "hour_ampm": "AM", "temperature": 6 },
    { "hour_number": 2, "hour_ampm": "AM", "temperature": 5 },
    { "hour_number": 3, "hour_ampm": "AM", "temperature": 6 },
    { "hour_number": 4, "hour_ampm": "AM", "temperature": 5 },
    { "hour_number": 5, "hour_ampm": "AM", "temperature": 6 },
    { "hour_number": 6, "hour_ampm": "AM", "temperature": 5 },
    { "hour_number": 7, "hour_ampm": "AM", "temperature": 6 },
    { "hour_number": 8, "hour_ampm": "AM", "temperature": 5 },
    { "hour_number": 9, "hour_ampm": "AM", "temperature": 6 },
    { "hour_number": 10, "hour_ampm": "AM", "temperature": 5 },
    { "hour_number": 11, "hour_ampm": "AM", "temperature": 6 },
    { "hour_number": 12, "hour_ampm": "PM", "temperature": 5 },
    { "hour_number": 1, "hour_ampm": "PM", "temperature": 6 },
    { "hour_number": 2, "hour_ampm": "PM", "temperature": 5 },
    { "hour_number": 3, "hour_ampm": "PM", "temperature": 6 },
    { "hour_number": 4, "hour_ampm": "PM", "temperature": 5 },
    { "hour_number": 5, "hour_ampm": "PM", "temperature": 6 },
    { "hour_number": 6, "hour_ampm": "PM", "temperature": 5 },
    { "hour_number": 7, "hour_ampm": "PM", "temperature": 6 },
    { "hour_number": 8, "hour_ampm": "PM", "temperature": 5 },
    { "hour_number": 9, "hour_ampm": "PM", "temperature": 6 },
    { "hour_number": 10, "hour_ampm": "PM", "temperature": 5 },
    { "hour_number": 11, "hour_ampm": "PM", "temperature": 6 }
]

### TODO: Need function to retrieve all the valid user name
### TODO: Need function to get the current month event for a specific username
### TODO: Need function to get today's detail
### TODO: Need function to get today's hourly tempertature

@app.route("/")
def homepage():
    username = request.args.get("username", "")
    valid_usernames = ["Cindracindra", "Test1", "Test2"] # get_valid_users()

    now = datetime.now()
    today_detail = {
        "day": calendar.day_name[now.weekday()],
        "date": now.day,
        "month": calendar.month_name[now.month],
        "year": now.year
    }

    if username:
        event_list = current_month_event # get_events_for_user(username) 
    else:
        event_list = []

    return render_template(
        "index.html",
        calendar_matrix=get_month_calendar_matrix_weather(today_detail['year'], now.month),
        today_detail=today_detail,
        username=username,
        valid_usernames=valid_usernames,
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
    
    # all_event = get_events_for_user(username) 
    selected_event = None
    
    # Find event by ID
    for day in all_event:
        for event in day["daily_events"]:
            if str(event["id"]) == str(selected_event_id):
                selected_event = event
                break
    
    return render_template(
        "event_management.html", 
        username=username,
        all_event=all_event,
        selected_event=selected_event) 

@app.route("/management/load-event/<int:event_id>", methods=["POST"])
def web_load_event(event_id):
    username = request.form.get("username", "")
    return redirect(url_for("management", username=username, selected_event_id=event_id))


### TODO: Need function to get all events for a specific username
### TODO: Need the app route for edit
@app.route("/management/edit-event/<int:event_id>", methods=["POST"])
def web_edit_event(event_id):
    username = request.form.get("username", "")
    data = request.form
    ### edit_event(data)
    return redirect(url_for("management", username=username))


@app.route("/management/create-event", methods=["POST"])
def web_create_event():
    username = request.form.get("username", "")
    data = request.form
    # edit_event(data)
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
