import json
import requests
from requests import Response
from typing import List, Dict
from datetime import datetime, date
from functools import lru_cache

def weather_code_to_info(code, code_data):
    code_str = str(code) # is it needed to have error handling here?
    info = code_data.get(code_str)
    if info:
        return info['icon'], info['label']
        #return code_data.get(code_str)['icon'], code_data.get(code_str)['label']
        # what is the difference between .get and indexing directly?

    return None, None

@lru_cache(maxsize=1)
def _load_code_icons():
    with open("static/data/code_icon.json", "r") as f:
        return json.load(f)


def get_current_temperature_weather_code():
    url: str = "https://api.open-meteo.com/v1/forecast"

    daily = ["temperature_2m", "weather_code"]

    params = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "current": ",".join(daily),
        "timezone": "Europe/London"
    }

    response: Response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching current temperature: {response.status_code}")
    
    data = response.json()
    current_temp = data.get("current", {}).get("temperature_2m", None)
    current_weather_code = data.get("current", {}).get("weather_code", None)
    current_temp = round(current_temp) if current_temp is not None else None
    return current_temp, current_weather_code

def get_current_temperature_weather_code_with_icon():
    current_dict = {}
    temp, code = get_current_temperature_weather_code()

    code_data = _load_code_icons()

    icon, label = weather_code_to_info(code, code_data)

    weather_codes_dict = {"code": code, "icon": icon, "label": label}

    current_dict["temperature"] = temp
    current_dict["weather"] = weather_codes_dict

    return current_dict

def get_hourly_temp_weather_code_today():
    url: str = "https://api.open-meteo.com/v1/forecast"

    hourly = ["temperature_2m", "weather_code"]

    params = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "hourly": ",".join(hourly),
        "timezone": "Europe/London",
        "forecast_days": 1,
    }

    response: Response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching current temperature: {response.status_code}")
    
    data = response.json()
    hourly_temp = data.get("hourly", {}).get("temperature_2m", [])
    hourly_weather_code = data.get("hourly", {}).get("weather_code", [])
    if hourly_temp:
        hourly_temp = [round(t) for t in hourly_temp]
    
    return hourly_temp, hourly_weather_code

    
def get_hourly_weather():
    hourly_temp_list, hourly_weather_code_list = get_hourly_temp_weather_code_today()
    code_data = _load_code_icons()

    hourly_weather_list = []
    for i in range(len(hourly_temp_list)):
        temp = hourly_temp_list[i]


        code = hourly_weather_code_list[i]

        icon, label = weather_code_to_info(code, code_data)

        weather_codes_dict = {"code": code, "icon": icon, "label": label}

        weather_dict = {"temperature": temp, "weather_code": weather_codes_dict}
        hourly_weather_list.append(weather_dict)

    return hourly_weather_list

def get_max_min_temperature_today():
    url: str = "https://api.open-meteo.com/v1/forecast"

    daily = ["temperature_2m_max", "temperature_2m_min"]

    params = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "daily": ",".join(daily),
        "timezone": "Europe/London"
    }

    response: Response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching daily max/min temperature: {response.status_code}")
    
    data = response.json()
    daily = data.get("daily", {})
    max_temps_list = daily.get("temperature_2m_max", [])
    max_temps = max_temps_list[0] if max_temps_list else None

    min_temps_list = daily.get("temperature_2m_min", [])
    min_temps = min_temps_list[0] if min_temps_list else None
    
    max_temps = round(max_temps) if max_temps is not None else None
    min_temps = round(min_temps) if min_temps is not None else None

    return max_temps, min_temps

# could do time based caching here if needed
def get_weather_icon_daily():
    url: str = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "daily": "weather_code",
        "timezone": "Europe/London",
        "forecast_days": 16
    }

    response: Response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching weather code: {response.status_code}")
    
    weather_codes_dict = {}

    data = response.json()
    daily = data.get("daily", {})
    dates_list = daily.get("time", [])
    weather_codes_list = daily.get("weather_code", [])
    for i in range(len(dates_list)):
        date_str = dates_list[i]
        # date_obj = date.fromisoformat(date_str), this is pretty slow, not useful here, not doing bigger or smaller comparison
        code = weather_codes_list[i]
        weather_codes_dict[date_str] = code
    # weather_code = weather_codes_list[0] if weather_codes_list else None
    return weather_codes_dict
    # return a dict(date string: weather code int)



#note,
# initially returning a list, which preserve order, as there is no lookup needed
# but then there is problem when the list consist a change of month, e.g., end of Jan to beginning of Feb
# so a dict is needed for lookup by date instead of sequential access