import pytest


@pytest.fixture(autouse=True)
def clear_cache_before_test():
    """Clear cache before each test to prevent interference between tests."""
    from utils.cache import clear_cache
    from services.weather_service import reset_forecast_cache
    clear_cache()
    reset_forecast_cache()
    yield
    clear_cache()


@pytest.fixture
def sample_weather_code_data():
    """Sample weather code icon data for testing."""
    return {
        "0": {"icon": "clear-day.svg", "label": "Clear"},
        "61": {"icon": "rain.svg", "label": "Rain"},
        "81": {"icon": "rain.svg", "label": "Rain"},
        "3": {"icon": "cloudy.svg", "label": "Cloudy"},
    }


@pytest.fixture
def sample_current_weather_response():
    """Sample API response for current weather."""
    return {
        "current": {
            "temperature_2m": 15.7,
            "weather_code": 61
        }
    }


@pytest.fixture
def sample_hourly_forecast_response():
    """Sample API response for hourly forecast today."""
    return {
        "hourly": {
            "temperature_2m": [14.5, 15.2, 16.0, 15.8],
            "weather_code": [0, 3, 61, 81]
        }
    }


@pytest.fixture
def sample_daily_weather_response():
    """Sample API response for daily forecast."""
    return {
        "daily": {
            "time": ["2025-12-01", "2025-12-02", "2025-12-03"],
            "weather_code": [0, 61, 3]
        }
    }


@pytest.fixture
def sample_holiday_response():
    """Sample API response for public holidays."""
    return [
        {
            "date": "2025-12-25",
            "localName": "Christmas Day",
            "name": "Christmas Day",
            "countryCode": "GB",
            "fixed": False,
            "global": True,
            "counties": None,
            "launchYear": None,
            "types": ["Public"]
        },
        {
            "date": "2025-12-26",
            "localName": "Boxing Day",
            "name": "St. Stephen's Day",
            "countryCode": "GB",
            "fixed": False,
            "global": True,
            "counties": None,
            "launchYear": None,
            "types": ["Public"]
        }
    ]
