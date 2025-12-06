"""
Weather service - Business logic for weather data.

This module provides functions for retrieving and processing
weather information.It transforms raw API data into structured
WeatherReading and WeatherCode objects with human-readable
labels and icons.
"""

from utils.converters import (
    round_temperature,
    round_temperatures,
    weather_code_to_info,
)
from api import weather_api
from models.api_models.weather import WeatherCode, WeatherReading
from typing import List, Dict


def get_current_weather() -> WeatherReading:
    """
    Get current weather conditions with icon and label.

    Returns:
        WeatherReading object containing:
        - temperature: Rounded temperature in Celsius
        - weather_code: WeatherCode with code, icon, and label

    Note:
        This function is typically called by Flask routes to provide
        current weather data for the UI.
    """
    # Fetch raw weather data from API
    data = weather_api.fetch_current_weather()

    # Extract current weather values
    current = data.get("current", {})
    temp = current.get("temperature_2m", None)
    code = current.get("weather_code", None)

    # Round temperature to nearest integer
    rounded_temp = round_temperature(temp)

    # Convert weather code to human-readable info
    if code is not None:
        icon, label = weather_code_to_info(code)
    else:
        icon, label = None, None

    # Build weather code object
    weather_code = WeatherCode(code=code, icon=icon, label=label)

    # Return structured weather reading
    return WeatherReading(temperature=rounded_temp, weather_code=weather_code)


def get_hourly_forecast_today() -> List[WeatherReading]:
    """
    Get hourly weather forecast for today (24 hours).

    Fetches hourly forecast data from Open-Meteo API, processes each hour's
    data, and returns a list of WeatherReading objects with icons and labels.

    Returns:
        List of 24 WeatherReading objects, one for each hour of the day.
        Each reading contains rounded temperature and weather code info.

    Note:
        This function is typically called by Flask routes to display
        hourly forecast charts or tables in the UI.
    """
    # Fetch raw hourly forecast data from API
    data = weather_api.fetch_hourly_forecast_today()

    # Extract hourly temperature and weather code arrays
    hourly = data.get("hourly", {})
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weather_code", [])

    # Process each hour's data
    hourly_forecast = []
    rounded_temps = round_temperatures(temps)

    for temp, code in zip(rounded_temps, codes):
        # Convert weather code to human-readable info
        icon, label = weather_code_to_info(code)
        weather_code = WeatherCode(code=code, icon=icon, label=label)

        # Create weather reading for this hour
        hourly_forecast.append(
            WeatherReading(temperature=temp, weather_code=weather_code)
        )
    return hourly_forecast


# Called internally by calendar_service.py
def get_daily_forecast() -> Dict[str, WeatherCode]:
    """
    Get daily weather forecast for the next 16 days.

    Fetches daily forecast data from Open-Meteo API and processes
    it into a dictionary mapping date strings to WeatherCode objects.
    This function is used internally by calendar_service to add weather
    icons to calendar days.

    Returns:
        Dictionary mapping ISO date strings (YYYY-MM-DD) to WeatherCode
        objects. Each WeatherCode contains the weather condition code,
        icon, and label for that day.
    """
    data = weather_api.fetch_daily_forecast()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])

    weather_codes = {}

    for date_str, code in zip(dates, codes):
        icon, label = weather_code_to_info(code)
        weather_codes[date_str] = WeatherCode(
            code=code, icon=icon, label=label
        )

    return weather_codes
