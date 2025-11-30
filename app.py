from flask import Flask, render_template, request, redirect, url_for, jsonify

from api.event_api import get_events, create_event, delete_event
from api.profile_api import get_profiles, create_profile, delete_profile
from api.event_profile_api import (
    get_event_profiles,
    create_event_profile,
    delete_event_profile,
)

app = Flask(__name__)

events = {
        3: ["Doctor Appointment", "Lunch with XXX"],
        7: ["Project Deadline for SSE"],
        12: ["Birthday"],
        20: ["Team Meeting"]
    }

@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/management")
def management():
    return render_template("index.html")  # replace with proper html file


@app.route("/management/create-event", methods=["POST"])
def web_create_event():
    data = request.form
    create_event(data)
    return redirect(url_for("management"))


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
