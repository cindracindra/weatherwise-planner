"""Suggestions: which of an account's places suit which forecast days.

Each day (and, where the forecast has them, each hour) is one kind of
weather: sunny, dry but cloudy, rain likely, or snow and storms. A place
fits a kind well (GREAT), acceptably (OKAY) or not (POOR):

    weather        place ticks it        otherwise
    sunny/cloudy   GREAT                 OKAY (any place is fine when dry)
    rain likely    GREAT (an indoor pick) POOR
    snow, storms   OKAY if indoors        POOR

A place that ticks all three suits any weather, so no day is special for
it: it is OKAY every day, and only great fits are put forward.

A temperature outside the place's range, or strong wind at an outdoor
place, lowers the fit one step; an outdoor place after dark doesn't fit.
For each place the best time for a visit of its usual length is searched
hour by hour inside the account's window (after work on weekdays, most of
the day at weekends); without hourly forecast the day as a whole is
judged.

Nothing here touches the database or the web: callers pass in the
forecast, the places, the preferences and when the account is busy.
"""

import math
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional, Set

from models.api_models.suggestion import (
    CLOUDY, FIT_ORDER, GREAT, OKAY, POOR, RAINY, SEVERE, SUNNY,
    DayPlan, Preferences, Suggestion,
)
from models.api_models.weather import DayOutlook, HourOutlook

SNOW_CODES = {71, 73, 75, 77, 85, 86}
RAIN_CODES = set(range(51, 68)) | {80, 81, 82}
WET_CHANCE = 50     # % chance of rain from which a day counts as wet
SUNNY_CHANCE = 20   # % below which a clear day counts as sunny
WINDY = 40          # km/h of wind that spoils an outdoor visit
TODAY_LEAD = 1      # hours from now before a suggestion today may start


# ---------- Weather kinds and fits ----------

def classify(code: Optional[int], rain_chance: Optional[int]) -> str:
    """The kind of weather for a WMO code and chance of rain (None when
    the source has none: then the code alone decides)."""
    if code is not None and (code in SNOW_CODES or code >= 95):
        return SEVERE
    if (code is not None and code in RAIN_CODES) or (
            rain_chance is not None and rain_chance >= WET_CHANCE):
        return RAINY
    if code in (0, 1) and (rain_chance is None or rain_chance < SUNNY_CHANCE):
        return SUNNY
    return CLOUDY


def any_weather(place) -> bool:
    return place.suits_sunny and place.suits_cloudy and place.suits_rainy


def base_fit(place, kind: str) -> str:
    """How well a place suits a kind of weather, before temperature."""
    if any_weather(place):
        return OKAY
    if kind == SUNNY:
        return GREAT if place.suits_sunny else OKAY
    if kind == CLOUDY:
        return GREAT if place.suits_cloudy else OKAY
    if kind == RAINY:
        return GREAT if place.suits_rainy else POOR
    return OKAY if place.suits_rainy else POOR


def lower(fit: str) -> str:
    return {GREAT: OKAY, OKAY: POOR, POOR: POOR}[fit]


def worse(a: str, b: str) -> str:
    return a if FIT_ORDER[a] >= FIT_ORDER[b] else b


def _adjust(place, fit: str, low: Optional[float], high: Optional[float],
            wind: Optional[float]) -> tuple[str, List[str]]:
    """Lower a fit for temperature outside the place's range, or strong
    wind outdoors; say why."""
    reasons = []
    if place.temp_min is not None and low is not None \
            and low < place.temp_min:
        fit = lower(fit)
        reasons.append(f"colder than {place.temp_min}°")
    elif place.temp_max is not None and high is not None \
            and high > place.temp_max:
        fit = lower(fit)
        reasons.append(f"warmer than {place.temp_max}°")
    if not place.suits_rainy and wind is not None and wind >= WINDY:
        fit = lower(fit)
        reasons.append("windy")
    return fit, reasons


def confidence(day: date, today: date) -> str:
    """How far ahead the forecast is, in words."""
    ahead = (day - today).days
    if ahead <= 2:
        return "Likely"
    if ahead <= 6:
        return "Possible"
    return "Early look"


# ---------- The best time on a day ----------

def _visit_hours(place, window_len: int) -> int:
    return max(1, min(window_len, math.ceil(place.visit_minutes / 60)))


def best_time(place, outlook: DayOutlook, start_hour: int, end_hour: int
              ) -> Optional[Suggestion]:
    """The best visit for a place on a day within [start_hour, end_hour),
    judged hour by hour; None if the forecast has no complete stretch of
    hours there (the caller then judges the whole day)."""
    hours: Dict[int, HourOutlook] = {
        h.hour: h for h in outlook.hours
        if h.code is not None and start_hour <= h.hour < end_hour
    }
    length = _visit_hours(place, end_hour - start_hour)
    best = None
    for first in range(start_hour, end_hour - length + 1):
        block = [hours.get(h) for h in range(first, first + length)]
        if any(h is None for h in block):
            continue
        kinds = [classify(h.code, h.rain_chance) for h in block]
        fit = GREAT
        for kind in kinds:
            fit = worse(fit, base_fit(place, kind))
        temps = [h.temperature for h in block if h.temperature is not None]
        low = min(temps) if temps else None
        high = max(temps) if temps else None
        fit, reasons = _adjust(place, fit, low, high, outlook.wind)
        dark = any(h.is_day is False for h in block)
        if dark and not place.suits_rainy:
            # Outdoors needs daylight
            fit = POOR
            reasons.append("after dark")
        wettest = max((h.rain_chance or 0) for h in block)
        # Worst kind in the block describes it
        kind = max(kinds, key=[SUNNY, CLOUDY, RAINY, SEVERE].index)
        rank = (FIT_ORDER[fit], wettest, first)
        if best is None or rank < best[0]:
            start = datetime.combine(outlook.day, datetime.min.time()) \
                + timedelta(hours=first)
            best = (rank, Suggestion(
                place=place, day=outlook.day, fit=fit, kind=kind,
                start=start,
                end=start + timedelta(minutes=place.visit_minutes),
                temperature=round(high) if high is not None else None,
                reasons=reasons, dark=dark,
            ))
    return best[1] if best else None


def judge_day(place, outlook: DayOutlook, start_hour: int, end_hour: int
              ) -> Suggestion:
    """The whole day judged at once, for when there are no hours to go
    by: the visit is placed at the start of the window."""
    kind = classify(outlook.weather_code.code, outlook.rain_chance)
    fit, reasons = _adjust(place, base_fit(place, kind),
                           outlook.low, outlook.high, outlook.wind)
    start = datetime.combine(outlook.day, datetime.min.time()) \
        + timedelta(hours=start_hour)
    return Suggestion(
        place=place, day=outlook.day, fit=fit, kind=kind, start=start,
        end=start + timedelta(minutes=place.visit_minutes),
        temperature=outlook.high, reasons=reasons,
    )


# ---------- Plans ----------

def plan_day(outlook: DayOutlook, places: Iterable, prefs: Preferences,
             now: datetime, busy: Optional[Set] = None) -> DayPlan:
    """Every place judged for one day, best first.

    busy holds the place ids (None for events not made from a place) of
    the account's events that day: a place already planned that day is
    not suggested again, and with skip_busy_days a day with any event
    gets no suggestions."""
    busy = busy or set()
    start_hour, end_hour = prefs.window(outlook.day)
    if outlook.day == now.date():
        # Today: only what can still start a little ahead of now
        start_hour = max(start_hour, now.hour + TODAY_LEAD)
    plan = DayPlan(
        outlook=outlook,
        kind=classify(outlook.weather_code.code, outlook.rain_chance),
        confidence=confidence(outlook.day, now.date()),
        busy=bool(busy),
    )
    if start_hour >= end_hour or (prefs.skip_busy_days and busy):
        return plan

    suggestions = []
    for place in places:
        place_id = getattr(place, "id", None)
        if place_id is not None and place_id in busy:
            continue
        found = best_time(place, outlook, start_hour, end_hour)
        if found is None and outlook.day != now.date():
            found = judge_day(place, outlook, start_hour, end_hour)
        if found is not None:
            suggestions.append(found)
    suggestions.sort(key=lambda s: (FIT_ORDER[s.fit],
                                    s.place.name.lower()))
    plan.suggestions = suggestions
    return plan


def plan_days(outlooks: Iterable[DayOutlook], places: List, prefs: Preferences,
              now: datetime, busy_by_day: Optional[Dict[date, Set]] = None
              ) -> List[DayPlan]:
    """A plan for every forecast day, in order (all days, whatever the
    preferences: callers filter with prefs.includes where they need to)."""
    busy_by_day = busy_by_day or {}
    return [
        plan_day(o, places, prefs, now, busy_by_day.get(o.day))
        for o in outlooks
    ]


def today_pick(plans: List[DayPlan], prefs: Preferences, now: datetime,
               evening_from: int = 17) -> Optional[DayPlan]:
    """The plan for the strip at the top of the home page: today if it
    has a great fit still ahead, otherwise (from the evening) tomorrow's.
    None if the strip is switched off or there is nothing great."""
    if not prefs.show_today:
        return None
    by_day = {p.day: p for p in plans}
    today = by_day.get(now.date())
    if today and today.has_great and prefs.includes(today.day):
        return today
    if now.hour >= evening_from:
        tomorrow = by_day.get(now.date() + timedelta(days=1))
        if tomorrow and tomorrow.has_great and prefs.includes(tomorrow.day):
            return tomorrow
    return None
