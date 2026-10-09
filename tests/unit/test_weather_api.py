"""Weather API: Open-Meteo in one call, MET Norway as the backup."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from api import weather_api
from api.weather_api import (
    WeatherAPIError, fetch_forecast, fetch_met_norway, fetch_open_meteo,
    met_symbol_to_wmo,
)
from config import Config

OPEN_METEO = {
    "current": {"temperature_2m": 14.2, "weather_code": 61},
    "hourly": {
        "time": ["2026-10-09T00:00", "2026-10-09T01:00"],
        "temperature_2m": [12.0, 11.5],
        "weather_code": [3, 61],
        "precipitation_probability": [10, 70],
    },
    "daily": {"time": ["2026-10-09", "2026-10-10"], "weather_code": [61, None]},
}

MET = {"properties": {"timeseries": [
    {"time": "2026-10-09T09:00:00Z", "data": {
        "instant": {"details": {"air_temperature": 16.9}},
        "next_1_hours": {"summary": {"symbol_code": "lightrainshowers_day"}},
        "next_6_hours": {"summary": {"symbol_code": "rain"}}}},
    {"time": "2026-10-09T11:00:00Z", "data": {
        "instant": {"details": {"air_temperature": 18.0}},
        "next_1_hours": {"summary": {"symbol_code": "cloudy"}},
        "next_6_hours": {"summary": {"symbol_code": "cloudy"}}}},
    {"time": "2026-10-12T00:00:00Z", "data": {
        "instant": {"details": {"air_temperature": 9.0}},
        "next_6_hours": {"summary": {"symbol_code": "clearsky_night"}}}},
]}}


def response(json=None, status=200):
    r = MagicMock()
    r.json.return_value = json
    r.raise_for_status.side_effect = (
        requests.HTTPError(f"{status} Client Error") if status >= 400 else None)
    return r


def test_open_meteo_is_one_request_with_everything():
    with patch("api.weather_api.requests.get", return_value=response(OPEN_METEO)) as get:
        bundle = fetch_open_meteo()
    get.assert_called_once()
    params = get.call_args.kwargs["params"]
    assert {"current", "hourly", "daily"} <= set(params)
    assert params["forecast_days"] == 16
    assert get.call_args.kwargs["headers"]["User-Agent"] == Config.USER_AGENT
    assert bundle["current"] == {"temperature": 14.2, "code": 61}
    assert bundle["hourly"][1] == {"time": datetime(2026, 10, 9, 1),
                                   "temperature": 11.5, "code": 61,
                                   "rain_chance": 70}
    assert bundle["daily"] == {"2026-10-09": 61}


def test_a_429_is_a_weather_api_error():
    with patch("api.weather_api.requests.get", return_value=response(status=429)):
        with pytest.raises(WeatherAPIError, match="429"):
            fetch_open_meteo()


def test_a_timeout_is_a_weather_api_error():
    with patch("api.weather_api.requests.get", side_effect=requests.Timeout("slow")):
        with pytest.raises(WeatherAPIError):
            fetch_open_meteo()


def test_met_norway_converts_to_the_same_shape_in_london_time():
    with patch("api.weather_api.requests.get", return_value=response(MET)):
        bundle = fetch_met_norway()
    assert bundle["source"] == "met-norway"
    assert bundle["current"] == {"temperature": 16.9, "code": 80}
    # 09:00 UTC is 10:00 in London (summer time); only hourly points kept
    assert [h["time"] for h in bundle["hourly"]] == [
        datetime(2026, 10, 9, 10), datetime(2026, 10, 9, 12)]
    assert all(h["rain_chance"] is None for h in bundle["hourly"])
    # A day's weather is the one nearest midday: 12:00 London is 'cloudy'
    assert bundle["daily"]["2026-10-09"] == 3
    assert bundle["daily"]["2026-10-12"] == 0


@pytest.mark.parametrize("symbol, code", [
    ("clearsky_day", 0), ("fair_night", 1), ("partlycloudy_day", 2),
    ("cloudy", 3), ("fog", 45), ("lightrain", 61), ("heavyrainshowers_day", 82),
    ("snow", 73), ("rainandthunder", 95), ("lightsleetshowersandthunder_day", 95),
    ("something-new", None), (None, None),
])
def test_met_symbols(symbol, code):
    assert met_symbol_to_wmo(symbol) == code


def test_backup_is_used_only_when_open_meteo_fails():
    with patch.object(weather_api, "fetch_open_meteo", return_value={"source": "open-meteo"}), \
         patch.object(weather_api, "fetch_met_norway") as met:
        assert fetch_forecast()["source"] == "open-meteo"
    met.assert_not_called()
    with patch.object(weather_api, "fetch_open_meteo", side_effect=WeatherAPIError("429")), \
         patch.object(weather_api, "fetch_met_norway", return_value={"source": "met-norway"}):
        assert fetch_forecast()["source"] == "met-norway"


def test_both_failing_raises():
    with patch.object(weather_api, "fetch_open_meteo", side_effect=WeatherAPIError("429")), \
         patch.object(weather_api, "fetch_met_norway", side_effect=WeatherAPIError("down")):
        with pytest.raises(WeatherAPIError):
            fetch_forecast()
