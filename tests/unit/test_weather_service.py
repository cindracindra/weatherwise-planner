"""Weather service: one shared forecast, and what happens when fetching fails."""

from datetime import datetime
from unittest.mock import patch

import pytest

from api.weather_api import WeatherAPIError
from services import weather_service
from services.weather_service import (
    get_current_weather, get_daily_forecast, get_forecast,
    get_hourly_forecast_today,
)

TODAY = datetime(2026, 10, 9)
BUNDLE = {
    "source": "open-meteo",
    "current": {"temperature": 14.6, "code": 61},
    "hourly": [
        {"time": datetime(2026, 10, 9, h), "temperature": 10 + h / 2,
         "code": 3 if h < 12 else 61, "rain_chance": h * 4}
        for h in range(24)
    ] + [{"time": datetime(2026, 10, 10, 0), "temperature": 9,
          "code": 0, "rain_chance": 0}],
    "daily": {"2026-10-09": 61, "2026-10-10": 0, "2026-10-11": 999},
}


@pytest.fixture(autouse=True)
def labels(sample_weather_code_data):
    with patch("utils.converters._load_code_icons",
               return_value=sample_weather_code_data):
        yield


@pytest.fixture
def clock():
    """Controls time.monotonic() inside the service."""
    now = {"t": 1000.0}
    with patch("services.weather_service.time.monotonic",
               side_effect=lambda: now["t"]):
        yield now


def fetch(*results):
    """Patch fetch_forecast to return/raise each result in turn."""
    def side_effect():
        result = results[min(side_effect.calls, len(results) - 1)]
        side_effect.calls += 1
        if isinstance(result, Exception):
            raise result
        return result
    side_effect.calls = 0
    return patch("services.weather_service.weather_api.fetch_forecast",
                 side_effect=side_effect)


# ---------- Turning the bundle into what pages use ----------

def test_current_weather():
    with fetch(BUNDLE):
        reading = get_current_weather()
    assert reading.temperature == 15
    assert reading.weather_code.code == 61
    assert reading.weather_code.label == "Rain"


def test_hourly_is_todays_24_hours_in_order():
    with fetch(BUNDLE):
        hours = get_hourly_forecast_today(TODAY)
    assert len(hours) == 24
    assert hours[0].temperature == 10 and hours[13].rain_chance == 52
    assert hours[12].weather_code.code == 61


def test_hourly_fills_hours_the_source_does_not_cover():
    partial = {**BUNDLE, "hourly": BUNDLE["hourly"][9:]}  # starts at 09:00
    with fetch(partial):
        hours = get_hourly_forecast_today(TODAY)
    assert len(hours) == 24
    assert hours[3].temperature is None and hours[3].weather_code.code is None
    assert hours[9].temperature is not None


def test_daily_skips_codes_without_a_label():
    with fetch(BUNDLE):
        daily = get_daily_forecast()
    assert set(daily) == {"2026-10-09", "2026-10-10"}
    assert daily["2026-10-09"].icon == "rain.svg"


def test_no_forecast_means_empty_views():
    with fetch(WeatherAPIError("429")):
        assert get_hourly_forecast_today(TODAY) == []
        assert get_daily_forecast() == {}
        assert get_current_weather().temperature is None


# ---------- One fetch, shared and kept ----------

def test_one_fetch_serves_all_three_views(clock):
    with fetch(BUNDLE) as fetcher:
        get_current_weather()
        get_hourly_forecast_today(TODAY)
        get_daily_forecast()
    assert fetcher.call_count == 1


def test_fresh_forecast_is_reused_then_refreshed(clock):
    with fetch(BUNDLE) as fetcher:
        get_forecast()
        clock["t"] += weather_service.FRESH_FOR - 1
        get_forecast()
        assert fetcher.call_count == 1
        clock["t"] += 2
        get_forecast()
        assert fetcher.call_count == 2


def test_failed_refresh_keeps_the_last_good_forecast(clock):
    with fetch(BUNDLE, WeatherAPIError("429")):
        get_forecast()
        clock["t"] += weather_service.FRESH_FOR + 1
        assert get_forecast() is BUNDLE


def test_after_a_failure_it_waits_before_asking_again(clock):
    with fetch(WeatherAPIError("429"), BUNDLE) as fetcher:
        assert get_forecast() is None
        clock["t"] += weather_service.RETRY_AFTER - 1
        assert get_forecast() is None
        assert fetcher.call_count == 1          # no hammering
        clock["t"] += 2
        assert get_forecast() is BUNDLE         # and it recovers


def test_a_forecast_too_old_is_not_shown(clock):
    with fetch(BUNDLE, WeatherAPIError("429")):
        get_forecast()
        clock["t"] += weather_service.STALE_FOR + 1
        assert get_forecast() is None
