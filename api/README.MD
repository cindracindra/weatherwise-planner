# API Layer - External API Clients

This directory contains client modules for external third-party APIs. These modules handle raw HTTP requests and return unprocessed JSON data.

## Overview

The API layer is responsible for:

- Making HTTP requests to external services
- Handling network errors and timeouts
- Returning raw API responses (no data transformation)
- Raising custom exceptions on failures

**Important:** This layer does NOT process or transform data. Data processing happens in the `services/` layer.

---

## Weather API (`weather_api.py`)

Client for the **Open-Meteo API** - provides weather forecasts and current conditions.

### API Documentation

- **Base URL:** `https://api.open-meteo.com/v1/forecast`
- **Official Docs:** https://open-meteo.com/en/docs
- **Rate Limits:** Free tier with no API key required
- **Timeout:** 10 seconds (configured in `Config.API_TIMEOUT`)

### Functions

#### `fetch_current_weather() -> Dict[str, Any]`

Fetches current weather conditions for London (location set in Config).

**Returns:**

```python
{
    'current': {
        'temperature_2m': 15.3,      # Temperature in Celsius
        'weather_code': 61            # WMO weather code (0-99)
    }
}
```

**Usage:**

```python
from api.weather_api import fetch_current_weather

data = fetch_current_weather()
temp = data['current']['temperature_2m']
code = data['current']['weather_code']
```

---

#### `fetch_hourly_forecast_today() -> Dict[str, Any]`

Fetches 24-hour weather forecast for today.

**Returns:**

```python
{
    'hourly': {
        'time': ['2025-12-01T00:00', '2025-12-01T01:00', ...],  # 24 timestamps
        'temperature_2m': [14.5, 15.0, 15.5, ...],              # 24 temperatures
        'weather_code': [61, 61, 80, ...]                       # 24 weather codes
    }
}
```

**Usage:**

```python
data = fetch_hourly_forecast_today()
noon_temp = data['hourly']['temperature_2m'][12]  # Temperature at noon
```

---

#### `fetch_daily_forecast() -> Dict[str, Any]`

Fetches 16-day daily weather forecast (for calendar display).

**Returns:**

```python
{
    'daily': {
        'time': ['2025-12-01', '2025-12-02', ...],  # 16 dates (YYYY-MM-DD)
        'weather_code': [0, 61, 80, ...]             # 16 weather codes
    }
}
```

**Usage:**

```python
data = fetch_daily_forecast()
first_date = data['daily']['time'][0]
first_code = data['daily']['weather_code'][0]
```

---

## Holiday API (`holiday_api.py`)

Client for the **Nager.Date API** - provides public holiday information for countries worldwide.

### API Documentation

- **Base URL:** `https://date.nager.at/api/v3/PublicHolidays`
- **Official Docs:** https://date.nager.at/Api
- **Rate Limits:** Free, no API key required
- **Timeout:** 10 seconds (configured in `Config.API_REQUEST_TIMEOUT`)

### Functions

#### `fetch_public_holidays(year: int | None = None, country_code: str = "GB") -> List[Dict[str, Any]]`

Fetches public holidays for a specific year and country.

**Parameters:**

- `year` (optional): Year to fetch (defaults to current year if None)
- `country_code` (optional): ISO 3166-1 alpha-2 country code (defaults to "GB" from Config)

**Returns:**

```python
[
    {
        'date': '2025-01-01',
        'localName': "New Year's Day",
        'name': "New Year's Day",
        'countryCode': 'GB',
        'fixed': True,
        'global': True,
        'counties': None,
        'launchYear': None,
        'types': ['Public']
    },
    {
        'date': '2025-12-25',
        'localName': 'Christmas Day',
        'name': 'Christmas Day',
        'countryCode': 'GB',
        'fixed': True,
        'global': True,
        'counties': None,
        'launchYear': None,
        'types': ['Public']
    },
    ...
]
```

**Usage:**

```python
from api.holiday_api import fetch_public_holidays

# Get holidays for current year (default GB)
holidays = fetch_public_holidays()

# Get holidays for specific year and country
holidays_2026_us = fetch_public_holidays(year=2026, country_code="US")
```

---

## Related Documentation

- **Service Layer:** `../services/` - Processes API data and adds business logic
- **Models:** `../models/api_models/` - Data structures for API responses
- **Config:** `../config.py` - Centralized configuration
- **Tests:** `../tests/unit/` - Unit tests with mocked API calls
