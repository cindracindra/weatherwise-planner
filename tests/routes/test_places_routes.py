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
    assert "Next great: Sat 17 Oct, 09:00" in page


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


# ---------- From a suggestion to an event, and back ----------

SUGGESTION = {"placeid": "3", "start": "2026-10-17T11:00:00",
              "end": "2026-10-17T13:00:00", "next": "/?day=2026-10-17"}


def test_one_click_adds_the_event_at_the_place(client):
    with patch("routes.places_routes.get_place_by_id", return_value=ok(PLACE_JSON)), \
         patch("routes.places_routes.create_event",
               return_value=ok({"id": 41}, StatusCode.CREATED)) as create:
        response = client.post("/suggestions/add", data=SUGGESTION)
    data, user = create.call_args[0]
    assert user == USER and data["place_id"] == 3
    assert data["name"] == "Hyde Park"
    assert data["location"] == "Hyde Park, London W2"
    assert data["start_time"] == "2026-10-17T11:00:00"
    assert response.location.endswith("/?day=2026-10-17")
    with client.session_transaction() as session:
        assert session["added_event"]["id"] == 41
        assert session["added_event"]["text"] == \
            "Added Hyde Park, Sat 17 Oct 11:00-13:00."


def test_the_added_notice_shows_once_with_undo_and_change(client):
    with client.session_transaction() as session:
        session["added_event"] = {"id": 41, "name": "Hyde Park",
                                  "text": "Added Hyde Park, Sat 17 Oct 11:00-13:00."}
    with patch("routes.places_routes.get_preferences", return_value=Preferences()):
        page = client.get("/settings").data.decode()
        again = client.get("/settings").data.decode()
    assert "Added Hyde Park" in page and ">Undo<" in page
    assert "selected_eventid=41" in page
    assert "Added Hyde Park" not in again


def test_an_unknown_place_or_bad_times_add_nothing(client):
    with patch("routes.places_routes.get_place_by_id",
               return_value=ok({"error": "x"}, StatusCode.NOT_FOUND)), \
         patch("routes.places_routes.create_event") as create:
        client.post("/suggestions/add", data=SUGGESTION)
    create.assert_not_called()
    with patch("routes.places_routes.get_place_by_id", return_value=ok(PLACE_JSON)), \
         patch("routes.places_routes.create_event") as create:
        client.post("/suggestions/add", data=dict(SUGGESTION, end="2026-10-17T10:00"))
    create.assert_not_called()


def test_add_never_redirects_off_site(client):
    with patch("routes.places_routes.get_place_by_id", return_value=ok(PLACE_JSON)), \
         patch("routes.places_routes.create_event",
               return_value=ok({"id": 41}, StatusCode.CREATED)):
        response = client.post("/suggestions/add",
                               data=dict(SUGGESTION, next="https://evil.example/"))
    assert "evil.example" not in response.location


def test_undo_deletes_the_event_and_names_it(client):
    with patch("routes.places_routes.delete_event",
               return_value=ok({"message": "deleted"})) as delete:
        response = client.post("/suggestions/undo",
                               data={"eventid": "41", "name": "Hyde Park",
                                     "next": "/?day=2026-10-17#day-panel"})
    delete.assert_called_once_with(41, USER)
    assert response.location.endswith("#day-panel")
    assert flashes(client) == ["Removed Hyde Park from your calendar."]


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


def test_home_shows_todays_pick_and_good_days_ahead(home):
    page = home.get("/").data.decode()
    assert "Today, good for" in page and "Hyde Park" in page
    assert "Good days ahead" in page and "Sun 18" in page
    assert "good day for your places" in page            # the mark in the month


def test_choosing_a_day_opens_its_panel(home):
    page = home.get("/?day=2026-10-18").data.decode()
    assert 'id="day-panel"' in page and "Sunday 18 October" in page
    assert "Add event on this day" in page
    assert 'name="placeid" value="3"' in page             # the Add button


def test_a_day_past_the_forecast_says_so(home):
    page = home.get("/?day=2026-10-30").data.decode()
    assert "No forecast yet" in page


def test_a_bad_day_is_ignored(home):
    page = home.get("/?day=someday").data.decode()
    assert 'id="day-panel"' not in page


def test_add_event_on_this_day_starts_the_form_there(client):
    with patch("routes.web_routes.get_events", return_value=ok({"events": []})):
        page = client.get("/management/event?day=2026-10-18").data.decode()
    assert 'value="2026-10-18T09:00"' in page


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
    assert places[1]["planned_today"] is True
    assert "leaflet@1.9.4" in page and "integrity=" in page
