"""Unit tests for services/weather_service.py - weather data transformation and business logic."""

from services.weather_service import (
    get_current_weather,
    get_hourly_forecast_today,
    get_daily_forecast
)
from models.api_models.weather import WeatherCode, WeatherReading


class TestGetCurrentWeather:
    """Test get_current_weather() - transforms raw API data to WeatherReading."""

    def test_get_current_weather_success(
            self,
            mocker,
            sample_current_weather_response,
            sample_weather_code_data
    ):
        """Test fetching and transforming current weather with rounded temperature."""
        mocker.patch(
            'services.weather_service.weather_api.fetch_current_weather',
            return_value=sample_current_weather_response
        )

        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        result = get_current_weather()

        assert isinstance(result, WeatherReading)
        assert result.temperature == 16
        assert isinstance(result.weather_code, WeatherCode)
        assert result.weather_code.code == 61
        assert result.weather_code.icon == "rain.svg"
        assert result.weather_code.label == "Rain"

    def test_get_current_weather_none_values(self, mocker):
        """Test handling None values from API response."""
        mocker.patch(
            'services.weather_service.weather_api.fetch_current_weather',
            return_value={
                "current": {"temperature_2m": None, "weather_code": None}
                }
        )

        result = get_current_weather()

        assert isinstance(result, WeatherReading)
        assert result.temperature is None
        assert isinstance(result.weather_code, WeatherCode)
        assert result.weather_code.code is None
        assert result.weather_code.icon is None
        assert result.weather_code.label is None


class TestGetHourlyForecastToday:
    """Test get_hourly_forecast_today() - transforms hourly forecast to list of WeatherReadings."""

    def test_get_hourly_forecast_today(
            self,
            mocker,
            sample_hourly_forecast_response,
            sample_weather_code_data
    ):
        """Test fetching and transforming hourly forecast data."""
        mocker.patch(
            'services.weather_service.weather_api.fetch_hourly_forecast_today',
            return_value=sample_hourly_forecast_response
        )

        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        result = get_hourly_forecast_today()

        assert isinstance(result, list)
        assert len(result) == 4
        assert all(isinstance(r, WeatherReading) for r in result)
        assert result[0].temperature == 14
        assert result[0].weather_code.code == 0


class TestGetDailyForecast:
    """Test get_daily_forecast() - transforms daily forecast to date-to-WeatherCode dict."""

    def test_get_daily_forecast_success(
        self,
        mocker,
        sample_daily_weather_response,
        sample_weather_code_data
    ):
        """Test fetching and transforming daily forecast with date keys."""
        mocker.patch(
            'services.weather_service.weather_api.fetch_daily_forecast',
            return_value=sample_daily_weather_response
        )

        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        result = get_daily_forecast()

        assert isinstance(result, dict)
        assert "2025-12-01" in result
        assert isinstance(result["2025-12-01"], WeatherCode)
        assert result["2025-12-01"].code == 0
        assert result["2025-12-01"].icon == "clear-day.svg"

    def test_get_daily_forecast_skips_days_without_code(
        self,
        mocker,
        sample_weather_code_data
    ):
        """Days with no weather code are left out, not given a None icon."""
        mocker.patch(
            'services.weather_service.weather_api.fetch_daily_forecast',
            return_value={
                "daily": {
                    "time": ["2026-10-20", "2026-10-21"],
                    "weather_code": [3, None]
                }
            }
        )
        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        result = get_daily_forecast()

        assert list(result) == ["2026-10-20"]
        assert result["2026-10-20"].icon == "cloudy.svg"
