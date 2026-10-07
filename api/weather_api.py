"""
Client for Open-Meteo weather API.

This module provides functions to fetch weather data from the Open-Meteo API
(https://open-meteo.com). It handles HTTP requests
and returns raw JSON responses
for current weather, hourly forecasts, and daily forecasts.
"""

import requests
from requests import Response
from config import Config
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class WeatherAPIError(Exception):
    """
    Custom exception raised when a weather API request fails.
    """
    pass


def _make_request(params: dict) -> Dict[str, Any]:
    """
    Internal private helper function to send a GET request
    to the Open-Meteo API.

    Args:
        params: Dictionary of query parameters to send with the request.
               Common parameters include:
               - latitude (float): Geographic coordinate
               - longitude (float): Geographic coordinate
               - current (str): Comma-separated list of
                                current weather variables
               - hourly (str): Comma-separated list of hourly variables
               - daily (str): Comma-separated list of daily variables
               - timezone (str): Timezone identifier (e.g., "Europe/London")
               - forecast_days (int): Number of days to forecast

    Returns:
        Dictionary containing the raw JSON response from the API.
        Structure varies based on requested parameters but typically includes:
        - current: Dict of current weather conditions
        - hourly: Dict of hourly forecast data with time-series arrays
        - daily: Dict of daily forecast data with time-series arrays

    Raises:
        WeatherAPIError: If the HTTP request fails, times out,
        or returns an error status.

    Example:
        >>> params = {
                "latitude": 51.5074,
                "longitude": -0.1278,
                "current": "temperature_2m,weather_code",
                "timezone": "Europe/London"
            }
    """
    try:
        # Make GET request with timeout from config
        response: Response = requests.get(
            Config.OPEN_METEO_BASE_URL,
            params=params,
            timeout=Config.API_TIMEOUT
        )

        # Raise exception for HTTP error status codes (4xx, 5xx)
        response.raise_for_status()

        # Parse and return JSON response
        return response.json()
    except requests.exceptions.Timeout:
        raise
    except requests.RequestException as e:
        # Wrap all requests exceptions in our custom exception
        raise WeatherAPIError(f"Weather API request failed: {e}") from e


def fetch_current_weather() -> Dict[str, Any]:
    """
    Fetch current weather conditions for London.

    Retrieves the current temperature and weather code from the Open-Meteo API
    for the location specified in Config (defaults to London).

    Returns:
        Dictionary containing current weather data
        with the following structure:
        {
            'current': {
                'temperature_2m': float,  # Temperature in Celsius
                'weather_code': int       # WMO weather code
            }
        }

    Raises:
        WeatherAPIError: If the API request fails.

    Example:
        >>> data = fetch_current_weather()
        >>> data['current']['temperature_2m']
        15.3
        >>> data['current']['weather_code']
        61

    Note:
        This function returns raw API data.
        For processed data with icons and labels,
        use weather_service.get_current_weather() instead.
    """
    # Get location coordinates from config
    latitude = Config.LONDON_LAT
    longitude = Config.LONDON_LON

    # Specify which current weather variables to fetch
    current = ["temperature_2m", "weather_code"]

    # Build request parameters
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(current),
        "timezone": Config.TIMEZONE
    }
    try:
        return _make_request(params)
    except requests.exceptions.Timeout:
        logger.warning("Current weather API timeout")
        return {"current": {"temperature_2m": None, "weather_code": None}}
    except WeatherAPIError as e:
        logger.error(f"Failed to fetch current weather: {e}")
        return {"current": {"temperature_2m": None, "weather_code": None}}


def fetch_hourly_forecast_today() -> Dict[str, Any]:
    """
    Fetch hourly weather forecast for today (24 hours).

    Retrieves hourly temperature and weather code forecasts for the current day
    from the Open-Meteo API for the location specified in Config.

    Returns:
        Dictionary containing hourly forecast data
        with the following structure:
        {
            'hourly': {
                'time': List[str],           # ISO timestamp for each hour
                'temperature_2m': List[float],  # Temperatures in Celsius
                'weather_code': List[int]       # WMO weather codes
            }
        }

    Raises:
        WeatherAPIError: If the API request fails.

    Example:
        >>> data = fetch_hourly_forecast_today()
        >>> len(data['hourly']['temperature_2m'])
        24
        >>> data['hourly']['temperature_2m'][12]  # Temperature at noon
        18.5
        >>> data['hourly']['weather_code'][12]
        3  # Overcast

    Note:
        Returns exactly 24 hours of data (today only).
        For processed data, use weather_service.get_hourly_forecast_today().
    """
    # Get location coordinates from config
    latitude = Config.LONDON_LAT
    longitude = Config.LONDON_LON

    # Specify which hourly weather variables to fetch
    hourly = ["temperature_2m", "weather_code", "precipitation_probability"]

    # Build request parameters for today only
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(hourly),
        "timezone": Config.TIMEZONE,
        "forecast_days": 1,  # Only today
    }

    try:
        return _make_request(params)
    except requests.exceptions.Timeout:
        logger.warning("Hourly forecast API timeout")
        return {"hourly": {"temperature_2m": [], "weather_code": []}}
    except WeatherAPIError as e:
        logger.error(f"Hourly forecast API error: {e}")
        return {"hourly": {"temperature_2m": [], "weather_code": []}}


def fetch_daily_forecast() -> Dict[str, Any]:
    """
    Fetch daily weather forecast for the next 16 days.

    Retrieves daily weather codes from the Open-Meteo API for the location
    specified in Config.

    Returns:
        Dictionary containing daily forecast data with the following structure:
        {
            'daily': {
                'time': List[str],        # Dates in ISO format (YYYY-MM-DD)
                'weather_code': List[int]  # WMO weather codes for each day
            }
        }

    Raises:
        WeatherAPIError: If the API request fails.

    Example:
        >>> data = fetch_daily_forecast()
        >>> len(data['daily']['weather_code'])
        16
        >>> data['daily']['time'][0]
        '2025-12-01'
        >>> data['daily']['weather_code'][0]
        61
    Note:
        This function fetches 16 days of weather codes
        to populate the calendar.
        For processed data, use weather_service.get_daily_forecast().
    """
    # Get location coordinates from config
    latitude = Config.LONDON_LAT
    longitude = Config.LONDON_LON

    # Build request parameters for 16-day forecast
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code",  # Only weather code, no temperature
        "timezone": Config.TIMEZONE,
        "forecast_days": 16
    }

    try:
        return _make_request(params)
    except requests.exceptions.Timeout:
        logger.warning("Daily forecast API timeout")
        return {"daily": {"time": [], "weather_code": []}}
    except WeatherAPIError as e:
        logger.error(f"Daily forecast API error: {e}")
        return {"daily": {"time": [], "weather_code": []}}
