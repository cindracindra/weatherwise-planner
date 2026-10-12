"""Suggestions: matching places against the forecast."""

from datetime import date, datetime
from types import SimpleNamespace

import pytest

from models.api_models.suggestion import (
    CLOUDY, GREAT, OKAY, POOR, RAINY, SEVERE, SUNNY, Preferences,
)
from models.api_models.weather import DayOutlook, HourOutlook, WeatherCode
from services.suggestion_service import (
    base_fit, best_time, classify, confidence, good_days_ahead, judge_day,
    plan_day, plan_days, today_pick,
)

SAT = date(2026, 10, 17)          # a Saturday
MON = date(2026, 10, 19)
NOW = datetime(2026, 10, 17, 8, 0)  # Saturday morning


def place(id=1, name="Hyde Park", sunny=True, cloudy=True, rainy=False,
          temp_min=None, temp_max=None, minutes=120):
    return SimpleNamespace(
        id=id, name=name, suits_sunny=sunny, suits_cloudy=cloudy,
        suits_rainy=rainy, temp_min=temp_min, temp_max=temp_max,
        visit_minutes=minutes)


PARK = place()
MUSEUM = place(id=2, name="British Museum", sunny=False, cloudy=False,
               rainy=True)


def outlook(day=SAT, code=0, rain=0, high=20, low=10, wind=10, hours=None,
            dark_from=None):
    """A day; hours maps hour -> (code, rain chance, temperature).
    dark_from marks the hours from then on as after dark."""
    if hours is None:
        hours = {h: (code, rain, high) for h in range(24)}
    return DayOutlook(
        day=day, weather_code=WeatherCode(code=code, icon=None, label=None),
        high=high, low=low, rain_chance=rain, wind=wind,
        hours=[HourOutlook(hour=h, code=c, rain_chance=r, temperature=t,
                           is_day=None if dark_from is None else h < dark_from)
               for h, (c, r, t) in sorted(hours.items())],
    )


# ---------- Kinds of weather ----------

@pytest.mark.parametrize("code, rain, kind", [
    (0, 0, SUNNY), (1, 10, SUNNY), (1, 30, CLOUDY), (2, 0, CLOUDY),
    (3, None, CLOUDY), (45, 0, CLOUDY), (0, 60, RAINY), (61, 10, RAINY),
    (81, None, RAINY), (73, 0, SEVERE), (95, 0, SEVERE), (0, None, SUNNY),
])
def test_classify(code, rain, kind):
    assert classify(code, rain) == kind


@pytest.mark.parametrize("p, kind, fit", [
    (PARK, SUNNY, GREAT), (PARK, CLOUDY, GREAT), (PARK, RAINY, POOR),
    (PARK, SEVERE, POOR),
    (MUSEUM, SUNNY, OKAY), (MUSEUM, RAINY, GREAT), (MUSEUM, SEVERE, OKAY),
    (place(cloudy=False), CLOUDY, OKAY),
])
def test_base_fit(p, kind, fit):
    assert base_fit(p, kind) == fit


def test_an_any_weather_place_is_never_what_makes_a_day_good():
    market = place(id=3, name="Borough Market", rainy=True)
    for kind in (SUNNY, CLOUDY, RAINY, SEVERE):
        assert base_fit(market, kind) == OKAY
    plan = plan_day(outlook(), [market, PARK], Preferences(), NOW)
    assert [s.place.name for s in plan.picks] == ["Hyde Park"]
    alone = plan_day(outlook(code=95), [market], Preferences(), NOW)
    assert [s.fit for s in alone.picks] == [OKAY]


def test_confidence_fades_with_distance():
    assert [confidence(date(2026, 10, d), SAT) for d in (17, 19, 20, 23, 24)] \
        == ["Likely", "Likely", "Possible", "Possible", "Early look"]


# ---------- The best time ----------

def test_best_time_avoids_the_wet_hours():
    hours = {h: (0, 0, 18) for h in range(24)}
    for h in (9, 10, 11):
        hours[h] = (61, 80, 15)
    s = best_time(PARK, outlook(hours=hours), 9, 18)
    assert s.fit == GREAT
    assert (s.start.hour, s.end.hour) == (12, 14)
    assert s.kind == SUNNY and s.temperature == 18


def test_best_time_uses_the_visit_length():
    s = best_time(place(minutes=90), outlook(), 9, 18)
    assert (s.start, s.end) == (datetime(2026, 10, 17, 9, 0),
                                datetime(2026, 10, 17, 10, 30))


def test_best_time_prefers_the_driest_great_block():
    hours = {h: (1, 15, 18) for h in range(24)}   # sunny, small chance
    hours[14] = hours[15] = (0, 0, 19)
    s = best_time(PARK, outlook(hours=hours), 9, 18)
    assert s.start.hour == 14


def test_best_time_needs_complete_hours():
    assert best_time(PARK, outlook(hours={}), 9, 18) is None
    assert best_time(PARK, outlook(hours={9: (0, 0, 20)}), 9, 18) is None


def test_whole_day_when_no_hours():
    s = judge_day(MUSEUM, outlook(code=63, rain=90, hours={}), 9, 18)
    assert s.fit == GREAT and s.kind == RAINY
    assert s.start == datetime(2026, 10, 17, 9)


# ---------- Daylight ----------

def test_outdoors_needs_daylight():
    s = best_time(PARK, outlook(dark_from=18), 16, 21)
    assert s.start.hour == 16 and s.fit == GREAT     # before dark
    evening = best_time(PARK, outlook(dark_from=18), 18, 21)
    assert evening.fit == POOR and "after dark" in evening.reasons
    assert evening.kind_label == "Clear"


def test_indoors_doesnt_mind_the_dark():
    s = best_time(MUSEUM, outlook(code=63, rain=90, dark_from=18), 18, 21)
    assert s.fit == GREAT and not s.reasons


# ---------- Temperature and wind ----------

def test_too_cold_lowers_one_step_and_says_why():
    s = best_time(place(temp_min=18), outlook(high=12), 9, 18)
    assert s.fit == OKAY and "colder than 18°" in s.reasons


def test_too_warm_lowers_one_step():
    s = best_time(place(temp_max=25), outlook(high=30), 9, 18)
    assert s.fit == OKAY and "warmer than 25°" in s.reasons


def test_wind_spoils_outdoors_only():
    windy = outlook(wind=55)
    assert best_time(PARK, windy, 9, 18).fit == OKAY
    assert best_time(MUSEUM, outlook(code=61, rain=90, wind=55), 9, 18).fit \
        == GREAT


def test_summary_reads_well():
    s = best_time(place(temp_min=25), outlook(high=20), 9, 18)
    assert s.summary == "Sunny 09:00-11:00, 20°; colder than 25°"


# ---------- Days ----------

def test_a_sunny_saturday_puts_the_park_first():
    plan = plan_day(outlook(), [MUSEUM, PARK], Preferences(), NOW)
    assert [s.place.name for s in plan.suggestions] == [
        "Hyde Park", "British Museum"]
    assert [s.place.name for s in plan.picks] == ["Hyde Park"]
    assert plan.has_great and plan.kind == SUNNY


def test_a_wet_day_puts_indoor_places_forward():
    plan = plan_day(outlook(code=63, rain=90), [PARK, MUSEUM],
                    Preferences(), NOW)
    assert [s.place.name for s in plan.picks] == ["British Museum"]
    assert plan.fit_for(1).fit == POOR


def test_okay_places_are_picks_only_when_nothing_is_great():
    plan = plan_day(outlook(), [MUSEUM], Preferences(), NOW)
    assert [s.fit for s in plan.picks] == [OKAY]


def test_weekdays_use_the_evening_window():
    plan = plan_day(outlook(day=MON), [PARK], Preferences(), NOW)
    assert plan.suggestions[0].start == datetime(2026, 10, 19, 18)


def test_a_too_short_window_is_capped():
    prefs = Preferences(weekday_start=18, weekday_end=19)
    s = plan_day(outlook(day=MON), [place(minutes=180)], prefs, NOW) \
        .suggestions[0]
    assert s.start.hour == 18   # an hour's search; the visit keeps its length


def test_today_only_suggests_what_is_still_ahead():
    late = datetime(2026, 10, 17, 15, 20)
    plan = plan_day(outlook(), [PARK], Preferences(), late)
    assert plan.suggestions[0].start.hour == 16
    evening = datetime(2026, 10, 17, 17, 30)
    assert plan_day(outlook(), [PARK], Preferences(), evening).suggestions \
        == []


def test_a_place_already_planned_that_day_is_not_suggested():
    plan = plan_day(outlook(), [PARK, MUSEUM], Preferences(), NOW, busy={1})
    assert [s.place.id for s in plan.suggestions] == [2]
    assert plan.busy


def test_skip_busy_days():
    prefs = Preferences(skip_busy_days=True)
    assert plan_day(outlook(), [PARK], prefs, NOW, busy={None}).suggestions \
        == []
    assert plan_day(outlook(), [PARK], prefs, NOW).suggestions


# ---------- What the pages show ----------

def plans(prefs=Preferences(), now=NOW):
    days = [outlook(day=date(2026, 10, d)) for d in range(17, 27)]
    days[2] = outlook(day=date(2026, 10, 19), code=63, rain=90)   # wet Monday
    return plan_days(days, [PARK], prefs, now)


def test_today_pick_is_today_when_great():
    assert today_pick(plans(), Preferences(), NOW).day == SAT


def test_today_pick_moves_to_tomorrow_in_the_evening():
    evening = datetime(2026, 10, 17, 18, 30)
    assert today_pick(plans(now=evening), Preferences(), evening).day \
        == date(2026, 10, 18)


def test_today_pick_respects_the_switch_and_the_days():
    assert today_pick(plans(), Preferences(show_today=False), NOW) is None
    weekdays = Preferences(days="01234")
    assert today_pick(plans(weekdays), weekdays, NOW) is None


def test_good_days_ahead_needs_a_great_fit():
    prefs = Preferences()
    only_okay = plan_days([outlook(day=date(2026, 10, 18))], [MUSEUM], prefs, NOW)
    assert only_okay[0].picks and good_days_ahead(only_okay, prefs, NOW) == []


def test_good_days_ahead_skips_today_bad_days_and_other_days():
    days = [p.day.day for p in good_days_ahead(plans(), Preferences(), NOW)]
    assert days == [18, 20, 21, 22, 23, 24]   # not 17 (today), not wet 19
    weekend = Preferences(days="56")
    assert [p.day.day for p in good_days_ahead(plans(weekend), weekend, NOW)] \
        == [18, 24]
