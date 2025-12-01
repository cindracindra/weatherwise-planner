import requests
from requests import Response
from config import Config
from typing import Dict, Any, List

class WeatherAPIError(Exception):
    """Raised when weather API requests fail."""
    pass

def _make_request(params: dict) -> Dict[str, Any]:
    try:
        response: Response = requests.get(
            Config.OPEN_METEO_BASE_URL,
            params=params,
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise WeatherAPIError(f"Weather API request failed: {e}")

def fetch_current_weather() -> Dict[str, Any]:
    latitude = Config.LONDON_LAT
    longitude = Config.LONDON_LON

    current = ["temperature_2m", "weather_code"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(current),
        "timezone": Config.TIMEZONE
    }
    return _make_request(params)

def fetch_hourly_forecast_today() -> Dict[str, Any]:
    latitude = Config.LONDON_LAT
    longitude = Config.LONDON_LON

    hourly = ["temperature_2m", "weather_code"]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(hourly),
        "timezone": Config.TIMEZONE,
        "forecast_days": 1,
    }

    return _make_request(params)

def fetch_daily_forecast() -> Dict[str, Any]:
    latitude = Config.LONDON_LAT
    longitude = Config.LONDON_LON

    params = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "daily": "weather_code",
        "timezone": "Europe/London",
        "forecast_days": 16
    }

    return _make_request(params)