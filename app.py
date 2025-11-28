from flask import Flask, render_template, request, redirect, url_for

from api.event_api import (
    get_events,
    get_profiles,
    get_event_profiles,
    create_event,
    create_event_profile,
)

app = Flask(__name__)


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


@app.route("/api/event-profiles", methods=["GET"])
def api_get_event_profiles():
    return get_event_profiles()


@app.route("/api/event-profiles", methods=["POST"])
def api_create_event_profile():
    data = request.json
    return create_event_profile(data)
