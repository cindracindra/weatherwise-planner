import requests
from requests import Response
from typing import List, Dict
from datetime import datetime, date
from functools import lru_cache

def get_current_temperature():
    url: str = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "current": "temperature_2m",
        "timezone": "Europe/London"
    }
    # https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.409996&current=temperature_2m&timezone=Europe%2FLondon

    response: Response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching current temperature: {response.status_code}")
    
    data = response.json()
    current_temp = data.get("current", {}).get("temperature_2m", None)
    current_temp = round(current_temp) if current_temp is not None else None
    return current_temp

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
        "timezone": "Europe/London"
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

# if __name__ == "__main__":
#     weather_code = get_weather_icon_daily()
#     print(f"Weather code in London: {weather_code}")


#note,
# initially returning a list, which preserve order, as there is no lookup needed
# but then there is problem when the list consist a change of month, e.g., end of Jan to beginning of Feb
# so a dict is needed for lookup by date instead of sequential access