from flask import Flask, render_template

from api.event_api import get_events, get_profiles, get_event_profiles

app = Flask(__name__)


@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/api/events", methods=["GET"])
def api_get_events():
    return get_events()


@app.route("/api/profiles", methods=["GET"])
def api_get_profiles():
    return get_profiles()


@app.route("/api/event-profiles", methods=["GET"])
def api_get_event_profiles():
    return get_event_profiles()
