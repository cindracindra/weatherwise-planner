from utils.converters import round_temperature, round_temperatures, weather_code_to_info
from api import weather_api
from models.api_models.weather import WeatherCode, WeatherReading
from typing import List, Dict

def get_current_weather() -> WeatherReading:

    data = weather_api.fetch_current_weather()

    current = data.get("current", {})
    temp = current.get("temperature_2m", None)
    code = current.get("weather_code", None)

    rounded_temp = round_temperature(temp)
    icon, label = weather_code_to_info(code) if code is not None else (None, None)

    weather_code = WeatherCode(code=code, icon=icon, label=label)

    return WeatherReading(
        temperature=rounded_temp,
        weather_code=weather_code
    )

def get_hourly_forecast_today() -> List[WeatherReading]:

    data = weather_api.fetch_hourly_forecast_today()

    hourly = data.get("hourly", {})
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weather_code", [])

    hourly_forecast = []
    rounded_temps = round_temperatures(temps)

    for temp, code in zip(rounded_temps, codes):
        icon, label = weather_code_to_info(code)
        weather_code = WeatherCode(code=code, icon=icon, label=label)

        hourly_forecast.append(
            WeatherReading(
                temperature=temp,
                weather_code=weather_code
            )
        )

    return hourly_forecast

def get_daily_forecast() -> Dict[str, WeatherCode]:

    data = weather_api.fetch_daily_forecast()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])

    weather_codes = {}

    for date_str, code in zip(dates, codes):
        ico, label = weather_code_to_info(code)
        weather_codes[date_str] = WeatherCode(code=code, icon=ico, label=label)

    return weather_codes