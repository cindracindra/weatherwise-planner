"""Tests for the places pages, settings, suggestions on the home page,
and turning a suggestion into an event."""

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app import create_app
from models.api_models.suggestion import Preferences
from models.api_models.weather import DayOutlook, HourOutlook, WeatherCode
from services.planner import AccountPlans
from services.suggestion_service import plan_days
from utils.response import StatusCode, build_response

USER = 7
NOW = datetime(2026, 10, 17, 8, 0)   # Saturday morning
PARK = SimpleNamespace(
    id=3, name="Hyde Park", category="park", address="Hyde Park, London W2",
    latitude=None, longitude=None, notes=None, suits_sunny=True,
    suits_cloudy=True, suits_rainy=False, temp_min=None, temp_max=None,
    visit_minutes=120)
PLACE_JSON = {"id": 3, "name": "Hyde Park", "address": "Hyde Park, London W2"}


def sunny(day):
    return DayOutlook(
        day=day, weather_code=WeatherCode(code=0, icon=None, label="Clear"),
        high=21, low=11, rain_chance=0, wind=8,
        hours=[HourOutlook(hour=h, code=0, rain_chance=0, temperature=21,
                           is_day=7 <= h < 18) for h in range(24)])


def plans_with_park():
    outlooks = [sunny(date(2026, 10, d)) for d in (17, 18, 19)]
    return AccountPlans(now=NOW, prefs=Preferences(), places=[PARK],
                        plans=plan_days(outlooks, [PARK], Preferences(), NOW))


def ok(data, status=StatusCode.OK):
    return build_response(status, data)


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["LOGIN_DISABLED"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client, app.app_context():
        with patch("routes.places_routes.current_user_id", return_value=USER), \
             patch("routes.web_routes.current_user_id", return_value=USER):
            yield client


def flashes(client):
    with client.session_transaction() as session:
        return [m for _, m in session.get("_flashes", [])]


# ---------- The places page ----------

def test_places_page_lists_places_with_their_fit_and_next_great_day(client):
    with patch("routes.places_routes.list_places", return_value=[PARK]), \
         patch("routes.places_routes.account_plans", return_value=plans_with_park()):
        response = client.get("/places")
    page = response.data.decode()
    assert response.status_code == 200
    assert "Hyde Park" in page and "New place" in page
    assert "Today" in page and "Great" in page          # icon and word
    assert "Next great: Sun 18 Oct, 09:00" in page      # today has its own line


def test_places_page_with_no_places_invites_you_to_add_one(client):
    with patch("routes.places_routes.list_places", return_value=[]), \
         patch("routes.places_routes.account_plans",
               return_value=AccountPlans(now=NOW, prefs=Preferences())):
        page = client.get("/places").data.decode()
    assert "No places yet" in page


def test_choosing_a_place_opens_it_in_the_form(client):
    with patch("routes.places_routes.list_places", return_value=[PARK]), \
         patch("routes.places_routes.account_plans", return_value=plans_with_park()), \
         patch("routes.places_routes.get_place_by_id",
               return_value=ok(dict(PLACE_JSON, category="park", suits_sunny=True,
                                    suits_cloudy=True, suits_rainy=False,
                                    temp_min=None, temp_max=None, notes=None,
                                    visit_minutes=120, latitude=None,
                                    longitude=None))) as get:
        page = client.get("/places?selected_placeid=3").data.decode()
    get.assert_called_once_with(3, USER)
    assert "Change place" in page and 'value="Hyde Park"' in page


def test_adding_a_place(client):
    with patch("routes.places_routes.create_place",
               return_value=ok(PLACE_JSON, StatusCode.CREATED)) as create:
        response = client.post("/places/create", data={"name": "Hyde Park"})
    assert create.call_args[0][1] == USER
    assert response.location.endswith("/places")
    assert flashes(client) == ["Added Hyde Park to your places."]


def test_a_refused_place_says_why(client):
    with patch("routes.places_routes.create_place",
               return_value=ok({"error": "Give the place a name."},
                               StatusCode.BAD_REQUEST)):
        client.post("/places/create", data={})
    assert flashes(client) == ["Give the place a name."]


def test_deleting_a_place_keeps_its_events(client):
    with patch("routes.places_routes.delete_place",
               return_value=ok({"message": "deleted"})) as delete:
        client.post("/places/delete", data={"placeid": "3"})
    delete.assert_called_once_with(3, USER)
    assert "Events you made from it are kept" in flashes(client)[0]


# ---------- Settings ----------

def test_settings_page_shows_the_defaults(client):
    with patch("routes.places_routes.get_preferences", return_value=Preferences()):
        page = client.get("/settings").data.decode()
    assert 'value="every" checked' in page
    assert '<option value="18" selected>18:00</option>' in page


def test_saving_settings(client):
    form = {"days": "weekends", "weekday_start": "18", "weekday_end": "21",
            "weekend_start": "9", "weekend_end": "18"}
    with patch("routes.places_routes.save_preferences") as save:
        client.post("/settings", data=form)
    user, prefs = save.call_args[0]
    assert user == USER and prefs.days == "56" and not prefs.show_today
    assert flashes(client) == ["Your settings are saved."]


def test_bad_settings_are_not_saved(client):
    with patch("routes.places_routes.save_preferences") as save:
        client.post("/settings", data={"days": "custom"})
    save.assert_not_called()
    assert flashes(client) == ["Choose at least one day for suggestions."]


# ---------- From a suggestion to the event form ----------

def form_page(client, query):
    with patch("routes.web_routes.get_events", return_value=ok({"events": []})), \
         patch("routes.web_routes.list_places", return_value=[PARK]), \
         patch("routes.web_routes.get_place_by_id",
               return_value=ok(dict(PLACE_JSON))) as get:
        page = client.get("/management/event" + query).data.decode()
    return page, get


def test_a_suggestion_opens_the_event_form_filled_in(client):
    page, get = form_page(
        client, "?place=3&start=2026-10-17T11:00&end=2026-10-17T13:30")
    get.assert_called_once_with(3, USER)
    assert "Filled in from a suggestion" in page
    assert 'value="Hyde Park"' in page                       # name
    assert 'name="date" class="input num" required value="2026-10-17"' in page
    assert 'value="11:00"' in page and 'value="13:30"' in page
    assert 'value="Hyde Park, London W2"' in page            # where
    assert '<option value="3" data-where="Hyde Park, London W2"\n                        selected>' in page


def test_a_bad_suggestion_link_opens_an_empty_form(client):
    page, _ = form_page(client, "?place=3&start=soon&end=later")
    assert "Filled in from a suggestion" not in page
    assert 'name="date" class="input num" required value=""' in page


def test_the_form_posts_a_date_and_two_times(client):
    with patch("routes.web_routes.create_event",
               return_value=ok({"id": 9}, StatusCode.CREATED)) as create:
        client.post("/management/event/create", data={
            "name": "Hyde Park", "date": "2026-10-17", "start_time": "11:00",
            "end_time": "13:30", "location": "Hyde Park", "place_id": "3"})
    data, user = create.call_args[0]
    assert data["start_time"] == datetime(2026, 10, 17, 11, 0)
    assert data["end_time"] == datetime(2026, 10, 17, 13, 30)
    assert data["place_id"] == "3" and user == USER


def test_add_event_on_this_day_starts_the_form_there(client):
    page, _ = form_page(client, "?day=2026-10-18")
    assert 'required value="2026-10-18"' in page
    assert 'value="09:00"' in page and 'value="10:00"' in page


# ---------- Suggestions on the home page ----------

@pytest.fixture
def home(client):
    def week(first):
        return SimpleNamespace(days=[
            SimpleNamespace(day=d if d <= 31 else 0, weather=None, holidays=[])
            for d in range(first, first + 7)])
    # The real calendar has every day of the month; these weeks hold 11-31
    calendar = SimpleNamespace(weeks=[week(11), week(18), week(25)])
    with patch("routes.web_routes.get_today_detail",
               return_value={"year": 2026, "month": 10, "day": 17, "hour": 8,
                             "day_name": "Saturday", "month_name": "October"}), \
         patch("routes.web_routes.get_full_calendar", return_value=calendar), \
         patch("routes.web_routes.get_hourly_forecast_today", return_value=[]), \
         patch("routes.web_routes.get_events",
               return_value=ok({"events": []})), \
         patch("routes.web_routes.events_between", return_value=[]), \
         patch("routes.web_routes.account_plans", return_value=plans_with_park()):
        yield client


def test_home_shows_what_today_is_good_for_beside_the_weather(home):
    page = home.get("/").data.decode()
    assert 'class="top"' in page and 'class="today"' in page
    assert "Today, good for" in page and "Hyde Park" in page
    assert "/management/event?place=3&amp;start=2026-10-17T09:00" in page
    assert "Good days ahead" not in page
    assert "good day for your places" in page            # the mark in the month


def test_the_side_goes_when_switched_off(home):
    plans = plans_with_park()
    plans.prefs = Preferences(show_today=False)
    with patch("routes.web_routes.account_plans", return_value=plans):
        page = home.get("/").data.decode()
    assert "top--full" in page and "Today, good for" not in page


def test_choosing_a_day_opens_its_panel(home):
    page = home.get("/?day=2026-10-18").data.decode()
    assert 'id="day-panel"' in page and "Sunday 18 October" in page
    assert "Add event on this day" in page
    assert "/management/event?place=3&amp;start=2026-10-18" in page  # Add


def test_a_day_past_the_forecast_says_so(home):
    page = home.get("/?day=2026-10-30").data.decode()
    assert "No forecast yet" in page


def test_a_bad_day_is_ignored(home):
    page = home.get("/?day=someday").data.decode()
    assert 'id="day-panel"' not in page


# ---------- The API ----------

def test_suggestions_api(client):
    with patch("routes.api_routes.account_plans", return_value=plans_with_park()), \
         patch("routes.api_routes.current_user_id", return_value=USER):
        body = client.get("/api/suggestions").get_json()
    first = body["data"]["days"][0]
    assert first["date"] == "2026-10-17" and first["in_your_days"]
    assert first["picks"] == [3]
    assert first["places"][0]["fit"] == "great"
    assert first["places"][0]["start_time"] == "2026-10-17T09:00:00"


def test_places_api_is_scoped_to_the_account(client):
    with patch("routes.api_routes.get_places",
               return_value=ok({"places": []})) as get, \
         patch("routes.api_routes.current_user_id", return_value=USER):
        client.get("/api/places")
    get.assert_called_once_with(USER)


# ---------- The map ----------

def test_address_search_route(client):
    with patch("routes.places_routes.geocode_api.search",
               return_value=[{"name": "Kew", "short": "Kew", "address": "Kew",
                              "latitude": 51.47, "longitude": -0.29}]) as search:
        body = client.get("/places/search?q=Kew Gardens").get_json()
    search.assert_called_once_with("Kew Gardens")
    assert body["results"][0]["latitude"] == 51.47


def test_address_search_failure_is_a_plain_message(client):
    from api.geocode_api import GeocodeError
    with patch("routes.places_routes.geocode_api.search",
               side_effect=GeocodeError("timeout")):
        response = client.get("/places/search?q=Kew")
    assert response.status_code == 502
    assert "isn't reachable" in response.get_json()["error"]


def test_google_maps_links_use_the_pin_or_the_address():
    from routes.places_routes import google_maps_urls
    pinned = SimpleNamespace(name="Kew", address=None, latitude=51.47, longitude=-0.29)
    assert google_maps_urls(pinned)["maps_url"] == \
        "https://www.google.com/maps/search/?api=1&query=51.47%2C-0.29"
    unpinned = SimpleNamespace(name="Hyde Park", address="London W2",
                               latitude=None, longitude=None)
    assert google_maps_urls(unpinned)["directions_url"] == \
        "https://www.google.com/maps/dir/?api=1&destination=Hyde+Park%2C+London+W2"


def test_places_page_gives_the_map_its_pins_safely(client):
    sneaky = SimpleNamespace(**dict(vars(PARK), id=9, name="</script><b>x",
                                    latitude=51.5, longitude=-0.1))
    plans = plans_with_park()
    plans.busy = {NOW.date(): {9}}
    with patch("routes.places_routes.list_places", return_value=[PARK, sneaky]), \
         patch("routes.places_routes.account_plans", return_value=plans):
        page = client.get("/places").data.decode()
    data = page.split('id="places-data">')[1].split("</script>")[0]
    assert "</script><b>" not in data          # escaped inside the JSON
    import json
    places = json.loads(data)["places"]
    assert places[0]["fit"] == "great" and places[0]["latitude"] is None
    assert places[0]["today_note"] is None
    assert places[1]["today_note"] == "Already planned today"
    assert "leaflet@1.9.4" in page and "integrity=" in page


def test_why_a_place_is_not_rated_today():
    from routes.places_routes import today_note
    plans = plans_with_park()
    today = plans.plan_for(NOW.date())
    plans.busy = {NOW.date(): {3}}
    assert today_note(PARK, today, plans) == "Already planned today"
    plans.busy = {}
    assert today_note(PARK, None, plans) == "No forecast for today"
    plans.now = datetime(2026, 10, 17, 17, 30)      # weekend hours end at 18
    assert today_note(PARK, today, plans) == "Your suggestion hours are over for today"
    plans.now = datetime(2026, 10, 17, 10, 0)
    assert today_note(PARK, today, plans) == "No forecast left for today's hours"
