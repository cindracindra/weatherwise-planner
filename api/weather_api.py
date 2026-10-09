"""
Weather API: fetches London's forecast from Open-Meteo, with MET Norway as
a backup.

One request to Open-Meteo returns the current conditions, the hourly
forecast and the daily forecast together. If Open-Meteo refuses or fails
(for example HTTP 429 when a shared hosting address has used up its free
allowance), the same forecast is fetched from MET Norway instead and
converted to the same shape and WMO weather codes.

Both sources return a "forecast bundle":

    {
        "source": "open-meteo" | "met-norway",
        "current": {"temperature": 14.2, "code": 61},
        "hourly": [{"time": datetime, "temperature": 14.2, "code": 61,
                    "rain_chance": 80}, ...],      # London time, naive
        "daily": {"2026-10-09": 61, ...},
    }

`rain_chance` is None when the source doesn't provide it (MET Norway has
no chance of precipitation for the UK).
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

import requests

from config import Config

logger = logging.getLogger(__name__)

LONDON = ZoneInfo(Config.TIMEZONE)


class WeatherAPIError(Exception):
    """Raised when no source could provide a forecast."""


def _get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """GET JSON, identifying the app as the services ask. Any failure
    (timeout, connection, HTTP error such as 429) is a WeatherAPIError."""
    try:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": Config.USER_AGENT},
            timeout=Config.API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as e:
        raise WeatherAPIError(str(e)) from e


# ---------- Open-Meteo ----------

def fetch_open_meteo() -> Dict[str, Any]:
    """Current, hourly and 16-day forecast from Open-Meteo in one call."""
    data = _get(Config.OPEN_METEO_BASE_URL, {
        "latitude": Config.LONDON_LAT,
        "longitude": Config.LONDON_LON,
        "current": "temperature_2m,weather_code",
        "hourly": "temperature_2m,weather_code,precipitation_probability",
        "daily": "weather_code",
        "timezone": Config.TIMEZONE,
        "forecast_days": 16,
    })
    current = data.get("current", {})
    hourly = data.get("hourly", {})
    rain = hourly.get("precipitation_probability") or []
    daily = data.get("daily", {})
    return {
        "source": "open-meteo",
        "current": {
            "temperature": current.get("temperature_2m"),
            "code": current.get("weather_code"),
        },
        "hourly": [
            {
                "time": datetime.fromisoformat(time),
                "temperature": temp,
                "code": code,
                "rain_chance": rain[i] if i < len(rain) else None,
            }
            for i, (time, temp, code) in enumerate(zip(
                hourly.get("time", []),
                hourly.get("temperature_2m", []),
                hourly.get("weather_code", []),
            ))
        ],
        "daily": {
            day: code
            for day, code in zip(daily.get("time", []),
                                 daily.get("weather_code", []))
            if code is not None
        },
    }


# ---------- MET Norway (backup) ----------

# MET Norway symbol (without _day/_night/_polartwilight) -> WMO weather code
MET_SYMBOL_TO_WMO = {
    "clearsky": 0, "fair": 1, "partlycloudy": 2, "cloudy": 3, "fog": 45,
    "lightrain": 61, "rain": 63, "heavyrain": 65,
    "lightrainshowers": 80, "rainshowers": 81, "heavyrainshowers": 82,
    "lightsleet": 66, "sleet": 67, "heavysleet": 67,
    "lightsleetshowers": 66, "sleetshowers": 67, "heavysleetshowers": 67,
    "lightsnow": 71, "snow": 73, "heavysnow": 75,
    "lightsnowshowers": 85, "snowshowers": 85, "heavysnowshowers": 86,
}


def met_symbol_to_wmo(symbol: Optional[str]) -> Optional[int]:
    """'lightrainshowers_day' -> 80; anything with thunder -> 95."""
    if not symbol:
        return None
    base = symbol.split("_")[0]
    if "thunder" in base:
        return 95
    return MET_SYMBOL_TO_WMO.get(base)


def _symbol(point: Dict[str, Any], *periods: str) -> Optional[str]:
    for period in periods:
        symbol = point["data"].get(period, {}).get("summary", {}).get(
            "symbol_code")
        if symbol:
            return symbol
    return None


def fetch_met_norway() -> Dict[str, Any]:
    """The same forecast from MET Norway (api.met.no), converted to
    Open-Meteo's shape and WMO codes, in London time."""
    data = _get(Config.MET_NORWAY_URL, {
        "lat": Config.LONDON_LAT, "lon": Config.LONDON_LON,
    })
    points = data.get("properties", {}).get("timeseries", [])
    if not points:
        raise WeatherAPIError("MET Norway returned no forecast")

    def local(point):
        utc = datetime.fromisoformat(point["time"].replace("Z", "+00:00"))
        return utc.astimezone(LONDON).replace(tzinfo=None)

    first = points[0]
    hourly = [
        {
            "time": local(p),
            "temperature": p["data"]["instant"]["details"].get(
                "air_temperature"),
            "code": met_symbol_to_wmo(_symbol(p, "next_1_hours")),
            "rain_chance": None,
        }
        for p in points if "next_1_hours" in p["data"]
    ]

    # A day's weather: the symbol nearest midday that London day
    by_day = defaultdict(list)
    for p in points:
        symbol = _symbol(p, "next_6_hours", "next_12_hours", "next_1_hours")
        if symbol:
            when = local(p)
            by_day[when.date().isoformat()].append(
                (abs(when.hour - 12), symbol))
    daily = {
        day: met_symbol_to_wmo(min(options)[1])
        for day, options in by_day.items()
        if met_symbol_to_wmo(min(options)[1]) is not None
    }

    return {
        "source": "met-norway",
        "current": {
            "temperature": first["data"]["instant"]["details"].get(
                "air_temperature"),
            "code": met_symbol_to_wmo(
                _symbol(first, "next_1_hours", "next_6_hours")),
        },
        "hourly": hourly,
        "daily": daily,
    }


# ---------- Either ----------

def fetch_forecast() -> Dict[str, Any]:
    """The forecast bundle from Open-Meteo, or MET Norway if Open-Meteo
    fails. Raises WeatherAPIError only if both fail."""
    try:
        return fetch_open_meteo()
    except WeatherAPIError as e:
        logger.warning("Open-Meteo failed (%s); trying MET Norway", e)
    try:
        return fetch_met_norway()
    except WeatherAPIError as e:
        logger.error("MET Norway failed too (%s); no forecast", e)
        raise
