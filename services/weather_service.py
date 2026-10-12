"""
Weather service - Business logic for weather data.

Turns the forecast bundle from api.weather_api into the WeatherReading and
WeatherCode objects the pages use. All three views (now, today by hour,
the next 16 days) come from one shared forecast, fetched at most every
FRESH_FOR.

When a fetch fails, the last good forecast keeps being shown for up to
STALE_FOR, and the next attempt waits RETRY_AFTER, so a temporary refusal
(such as HTTP 429) neither blanks the page nor makes the app ask again
on every page view.
"""

import time
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from api import weather_api
from models.api_models.weather import (
    DayOutlook, HourOutlook, WeatherCode, WeatherReading,
)
from utils.converters import round_temperature, weather_code_to_info

FRESH_FOR = 30 * 60        # seconds a forecast is reused
STALE_FOR = 12 * 60 * 60   # seconds an old forecast may stand in for a new one
RETRY_AFTER = 60           # seconds to wait after a failed fetch

# Times are time.monotonic() readings, or None for "never". (Not 0: the
# monotonic clock counts from boot, so on a machine up for under a minute
# 0 would look like a failure "just now" and the weather would be skipped.)
_state: Dict[str, Any] = {"bundle": None, "fetched": None, "failed": None}


def reset_forecast_cache() -> None:
    """Forget the stored forecast (for tests)."""
    _state.update(bundle=None, fetched=None, failed=None)


def get_forecast() -> Optional[Dict[str, Any]]:
    """The forecast bundle, or None if there is none to show."""
    now = time.monotonic()
    bundle = _state["bundle"]
    fetched, failed = _state["fetched"], _state["failed"]
    age = now - fetched if fetched is not None else float("inf")
    usable_old = bundle if age < STALE_FOR else None
    if bundle is not None and age < FRESH_FOR:
        return bundle
    if failed is not None and now - failed < RETRY_AFTER:
        return usable_old
    try:
        bundle = weather_api.fetch_forecast()
    except weather_api.WeatherAPIError:
        _state["failed"] = now
        return usable_old
    _state.update(bundle=bundle, fetched=now, failed=None)
    return bundle


def _code(code: Optional[int]) -> WeatherCode:
    icon, label = weather_code_to_info(code) if code is not None else (
        None, None)
    return WeatherCode(code=code, icon=icon, label=label)


def get_current_weather() -> WeatherReading:
    """The weather now: rounded temperature and conditions."""
    bundle = get_forecast()
    current = bundle["current"] if bundle else {}
    return WeatherReading(
        temperature=round_temperature(current.get("temperature")),
        weather_code=_code(current.get("code")),
    )


def get_hourly_forecast_today(
    today: Optional[datetime] = None,
) -> List[WeatherReading]:
    """Today's 24 hours (London), one WeatherReading per hour, in order.

    Hours the source doesn't cover (MET Norway starts at the current hour)
    have no temperature or code. Empty if there is no forecast at all."""
    bundle = get_forecast()
    if not bundle:
        return []
    today = (today or datetime.now(weather_api.LONDON)).date()
    by_hour = {
        h["time"].hour: h for h in bundle["hourly"]
        if h["time"].date() == today
    }
    if not by_hour:
        return []
    readings = []
    for hour in range(24):
        h = by_hour.get(hour, {})
        readings.append(WeatherReading(
            temperature=round_temperature(h.get("temperature")),
            weather_code=_code(h.get("code")),
            rain_chance=h.get("rain_chance"),
        ))
    return readings


def get_daily_forecast() -> Dict[str, WeatherCode]:
    """{"YYYY-MM-DD": WeatherCode} for the days the forecast covers. Days
    whose code has no label are left out, so the calendar never shows a
    broken icon."""
    bundle = get_forecast()
    if not bundle:
        return {}
    daily = {}
    for day, code in bundle["daily"].items():
        weather = _code(code)
        if weather.icon is not None:
            daily[day] = weather
    return daily


def get_day_outlooks(today: Optional[date] = None) -> List[DayOutlook]:
    """Every forecast day from today (London) onwards, in order, with its
    high, low, rain chance, wind and hours. Days without a weather code
    are left out, since nothing can be judged about them. Empty if there
    is no forecast."""
    bundle = get_forecast()
    if not bundle:
        return []
    today = today or datetime.now(weather_api.LONDON).date()
    details = bundle.get("days", {})
    hours_by_day = defaultdict(list)
    for h in bundle["hourly"]:
        hours_by_day[h["time"].date()].append(HourOutlook(
            hour=h["time"].hour,
            temperature=h.get("temperature"),
            code=h.get("code"),
            rain_chance=h.get("rain_chance"),
        ))

    outlooks = []
    for day_text, code in sorted(bundle["daily"].items()):
        day = date.fromisoformat(day_text)
        if day < today or code is None:
            continue
        info = details.get(day_text, {})
        outlooks.append(DayOutlook(
            day=day,
            weather_code=_code(code),
            high=round_temperature(info.get("high")),
            low=round_temperature(info.get("low")),
            rain_chance=info.get("rain_chance"),
            wind=info.get("wind"),
            hours=sorted(hours_by_day.get(day, []), key=lambda h: h.hour),
        ))
    return outlooks


def forecast_source() -> Optional[str]:
    """Which service the forecast on screen came from, if any."""
    bundle = _state["bundle"]
    return bundle["source"] if bundle else None
