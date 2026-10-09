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
from datetime import datetime
from typing import Any, Dict, List, Optional

from api import weather_api
from models.api_models.weather import WeatherCode, WeatherReading
from utils.converters import round_temperature, weather_code_to_info

FRESH_FOR = 30 * 60        # seconds a forecast is reused
STALE_FOR = 12 * 60 * 60   # seconds an old forecast may stand in for a new one
RETRY_AFTER = 60           # seconds to wait after a failed fetch

_state: Dict[str, Any] = {"bundle": None, "fetched": 0.0, "failed": 0.0}


def reset_forecast_cache() -> None:
    """Forget the stored forecast (for tests)."""
    _state.update(bundle=None, fetched=0.0, failed=0.0)


def get_forecast() -> Optional[Dict[str, Any]]:
    """The forecast bundle, or None if there is none to show."""
    now = time.monotonic()
    bundle = _state["bundle"]
    age = now - _state["fetched"]
    if bundle is not None and age < FRESH_FOR:
        return bundle
    if now - _state["failed"] < RETRY_AFTER:
        return bundle if bundle is not None and age < STALE_FOR else None
    try:
        bundle = weather_api.fetch_forecast()
    except weather_api.WeatherAPIError:
        _state["failed"] = now
        old = _state["bundle"]
        return old if old is not None and age < STALE_FOR else None
    _state.update(bundle=bundle, fetched=now, failed=0.0)
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


def forecast_source() -> Optional[str]:
    """Which service the forecast on screen came from, if any."""
    bundle = _state["bundle"]
    return bundle["source"] if bundle else None
