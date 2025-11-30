from flask import Flask, render_template, redirect, url_for, request

import calendar
from calendar import monthcalendar
from datetime import date, datetime

app = Flask(__name__)

events = {
        3: ["Doctor Appointment", "Lunch with XXX"],
        7: ["Project Deadline for SSE"],
        12: ["Birthday"],
        20: ["Team Meeting"]
    }

day_events = [
    {"id": 1, "title": "Meeting", "description": "Team sync", "start_hour": "10", "end_hour": "11", "duration": 1},
    {"id": 2, "title": "Workout", "description": "Gym session", "start_hour": "18", "end_hour": "18.5", "duration": 0.5},
    {"id": 2, "title": "Tesr", "description": "Gym session", "start_hour": "18.5", "end_hour": "19", "duration": 0.5}
    ]

full_event_list = [
    {"day": "Thursday, 27 November 2025", "daily_events": day_events},
    {"day": "Friday, 28 November 2025", "daily_events": []}
]


@app.route("/")
def homepage():
    current_date = datetime.now().day
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    month_name = calendar.month_name[current_month]
    day_name = "Monday"

    
    hourly_temp = [{ "hour_number": 12, "hour_ampm": "AM", "temperature": 5 },
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
    { "hour_number": 11, "hour_ampm": "PM", "temperature": 6 }]
    
    weeks = monthcalendar(current_year, current_month)
    return render_template(
        "index.html",
        weeks=weeks,
        month_name=month_name,
        current_year=current_year,
        events=events,
        day_name=day_name,
        current_date=current_date,
        hourly_temp=hourly_temp,
        day_events=day_events)


@app.route("/reload_calendar", methods=['GET'])
def reload_calendar():
    return redirect(url_for("homepage"))

@app.route("/manage_event", methods=["GET", "POST"])
def manage_event():
    
    selected_event = None
    if request.method == "POST":
        event_id = int(request.form.get("event_id"))
        
        # Find event by ID
        selected_event = None
        for i in full_event_list:
            for e in i["daily_events"]:
                if e["id"] == event_id:
                    selected_event = e
                    break

    return render_template("manage_event.html", full_event_list=full_event_list, selected_event=selected_event)