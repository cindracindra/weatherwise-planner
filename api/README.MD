## API Layer Documentation

The API layer contains client modules for external third-party APIs. These modules handle raw HTTP requests and return unprocessed JSON data.

### Responsibilities

The API layer is responsible for:

- Making HTTP requests to external services
- Handling network errors and timeouts
- Returning raw API responses (no data transformation)
- Raising custom exceptions on failures

**Important:** This layer does NOT process or transform data. Data processing happens in the `services/` layer.

### Weather API (`api/weather_api.py`)

Client for the **Open-Meteo API** - provides weather forecasts and current conditions.

#### API Documentation

- **Base URL:** `https://api.open-meteo.com/v1/forecast`
- **Official Docs:** https://open-meteo.com/en/docs
- **Rate Limits:** Free tier with no API key required
- **Timeout:** 10 seconds (configured in `Config.API_TIMEOUT`)

#### Functions

**`fetch_current_weather() -> Dict[str, Any]`**

Fetches current weather conditions for London (location set in Config).

Returns:

```python
{
    'current': {
        'temperature_2m': 15.3,      # Temperature in Celsius
        'weather_code': 61            # WMO weather code (0-99)
    }
}
```

**`fetch_hourly_forecast_today() -> Dict[str, Any]`**

Fetches 24-hour weather forecast for today.

Returns:

```python
{
    'hourly': {
        'time': ['2025-12-01T00:00', '2025-12-01T01:00', ...],  # 24 timestamps
        'temperature_2m': [14.5, 15.0, 15.5, ...],              # 24 temperatures
        'weather_code': [61, 61, 80, ...]                       # 24 weather codes
    }
}
```

**`fetch_daily_forecast() -> Dict[str, Any]`**

Fetches 16-day daily weather forecast (for calendar display).

Returns:

```python
{
    'daily': {
        'time': ['2025-12-01', '2025-12-02', ...],  # 16 dates (YYYY-MM-DD)
        'weather_code': [0, 61, 80, ...]             # 16 weather codes
    }
}
```

### Holiday API (`api/holiday_api.py`)

Client for the **Nager.Date API** - provides public holiday information for countries worldwide.

#### API Documentation

- **Base URL:** `https://date.nager.at/api/v3/PublicHolidays`
- **Official Docs:** https://date.nager.at/Api
- **Rate Limits:** Free, no API key required
- **Timeout:** 10 seconds (configured in `Config.API_REQUEST_TIMEOUT`)

#### Functions

**`fetch_public_holidays(year: int | None = None, country_code: str = "GB") -> List[Dict[str, Any]]`**

Fetches public holidays for a specific year and country.

Parameters:

- `year` (optional): Year to fetch (defaults to current year if None)
- `country_code` (optional): ISO 3166-1 alpha-2 country code (defaults to "GB" from Config)

Returns:

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
    ...
]
```

## API Models Documentation

This section contains data models (dataclasses) for external API responses. These models provide type-safe structures for data returned from third-party APIs.

### Overview

API models serve as:

- **Data Transfer Objects (DTOs)** - Structured representations of API responses
- **Type safety** - Ensure correct data types throughout the application
- **Serialization** - Convert between Python objects and JSON dictionaries
- **Documentation** - Self-documenting data structures with clear field types

**Important:** These models represent external API data, NOT database tables.

### Weather Models (`models/api_models/weather.py`)

#### `WeatherCode`

Represents a weather condition with its code, icon, and human-readable label.

**Fields:**

- `code: Optional[int]` - WMO weather code (0-99)
- `icon: Optional[str]` - Icon representation (path to svg)
- `label: Optional[str]` - Human-readable description

**Methods:**

- `to_dict() -> dict` - Converts to JSON-serializable dictionary

**Example:**

```python
from models.api_models.weather import WeatherCode

wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
wc_dict = wc.to_dict()
# {'code': 61, 'icon': 'rain.svg', 'label': 'Rain'}
```

#### `WeatherReading`

Represents a single weather measurement with temperature and conditions.

**Fields:**

- `temperature: Optional[int]` - Temperature in Celsius (rounded)
- `weather_code: WeatherCode` - Weather condition details

**Methods:**

- `to_dict() -> dict` - Converts to JSON-serializable dictionary

**Example:**

```python
from models.api_models.weather import WeatherCode, WeatherReading

wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
reading = WeatherReading(temperature=15, weather_code=wc)

reading_dict = reading.to_dict()
# {
#     'temperature': 15,
#     'weather_code': {
#         'code': 61,
#         'icon': 'rain.svg',
#         'label': 'Rain'
#     }
# }
```

### Holiday Models (`models/api_models/holiday.py`)

#### `Holiday`

Represents a public holiday with its date and name.

**Fields:**

- `date: date` - Holiday date (Python datetime.date object)
- `local_name: str` - Holiday name in local language

**Class Methods:**

- `from_api_response(cls, data: dict) -> Holiday` - Creates Holiday from raw API data

**Instance Methods:**

- `to_dict() -> dict` - Converts to JSON-serializable dictionary

### Calendar Models (`models/api_models/calendar.py`)

#### `CalendarDay`

Represents a single day in the calendar with optional holidays and weather.

**Fields:**

- `day: int` - Day of month (0 for empty cells, 1-31 for actual days)
- `holidays: List[str]` - List of holiday names (empty if no holidays)
- `weather: Optional[WeatherCode]` - Weather forecast (None if not available)

**Properties:**

- `is_empty: bool` - True if day == 0 (empty calendar cell)
- `is_holiday: bool` - True if holidays list is not empty

**Methods:**

- `to_dict() -> dict` - Converts to JSON-serializable dictionary

**Example:**

```python
from models.api_models.calendar import CalendarDay
from models.api_models.weather import WeatherCode

wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
holiday = CalendarDay(day=25, holidays=["Christmas Day"], weather=wc)

print(holiday.is_holiday)  # True
```

#### `CalendarWeek`

Represents a week in the calendar (always 7 days).

**Fields:**

- `days: List[CalendarDay]` - Exactly 7 CalendarDay objects

**Validation:**

- Raises `ValueError` if days list doesn't contain exactly 7 elements

**Methods:**

- `to_dict() -> List[dict]` - Converts to list of day dictionaries

#### `CalendarMonth`

Represents a complete month calendar with multiple weeks.

**Fields:**

- `year: int` - Year (e.g., 2025)
- `month: int` - Month number (1-12)
- `weeks: List[CalendarWeek]` - List of weeks (typically 4-6 weeks)
- `current_day: int` - Day to highlight (0 if not current month)

**Methods:**

- `to_dict() -> dict` - Converts to JSON-serializable dictionary

**Example:**

```python
from models.api_models.calendar import CalendarDay, CalendarWeek, CalendarMonth

days = [CalendarDay(day=i) for i in range(7)]
week = CalendarWeek(days=days)

month = CalendarMonth(year=2025, month=12, weeks=[week], current_day=15)
```

## Services Layer Documentation

The services layer contains business logic that transforms raw API data into application-ready data structures. Services orchestrate data from multiple sources and apply business rules, acting as an intermediary between the API layer and Flask routes.

### Service Layer Responsibilities

Services handle:

- **Data transformation:** Converting API responses to domain models
- **Business logic:** Rounding temperatures, formatting dates, combining data
- **Multi-source orchestration:** Combining holidays + weather + calendar matrix
- **Caching:** Using `@lru_cache` and `@timed_cache` to avoid redundant API calls

Services do NOT:

- Make HTTP requests directly (that's the API layer's job)
- Handle Flask request/response logic (that's the route's job)
- Contain UI logic or HTML generation

### Weather Service (`services/weather_service.py`)

Transforms raw weather API data into structured WeatherReading objects with human-readable labels and icons.

#### `get_current_weather() -> WeatherReading`

Fetches current weather conditions and adds weather code information (icon and label).

**Data Flow:**

```
weather_api.fetch_current_weather()
    → Returns: {"current": {"temperature_2m": 15.3, "weather_code": 61}}
    ↓
weather_service.get_current_weather()
    → Rounds temperature: 15.3 → 15
    → Converts code to info: 61 → ("rain.svg", "Rain")
    → Returns: WeatherReading(temperature=15, weather_code=WeatherCode(...))
```

#### `get_hourly_forecast_today() -> List[WeatherReading]`

Fetches 24-hour hourly forecast and processes each hour into WeatherReading objects.

#### `get_daily_forecast() -> Dict[str, WeatherCode]`

Fetches 16-day daily forecast as a dictionary mapping ISO date strings to WeatherCode objects. Used internally by calendar_service.

### Holiday Service (`services/holiday_service.py`)

Transforms raw holiday API data into organized, date-indexed structures for fast lookups.

#### `get_public_holidays(year: int = 2025, country_code: str = "GB") -> Dict[date, List[str]]`

Fetches all public holidays for a year and organizes them by date for efficient lookups.

**Features:**

- Caches results with `@lru_cache(maxsize=1)` to avoid redundant API calls
- Handles multiple holidays on the same day
- Returns regular dict (not defaultdict) for consistent behavior

#### `get_holidays_for_date(target_date: date, year: int = None) -> List[str]`

Convenience function to check if a specific date is a holiday.

### Calendar Service (`services/calendar_service.py`)

Orchestrates calendar generation by combining date matrices, holidays, and weather forecasts into rich CalendarMonth objects.

#### `get_current_month_year() -> tuple[int, int]`

Helper to get the current month and year for default calendar display.

#### `get_current_day_if_matches(year: int, month: int) -> int`

Returns the current day number if viewing the current month (for highlighting), otherwise 0.

#### `build_calendar_matrix(year: int, month: int) -> List[List[int]]`

Creates the base calendar grid with weeks as rows and days as columns.

**Example:**

```python
from services.calendar_service import build_calendar_matrix

matrix = build_calendar_matrix(2025, 12)
print(matrix[0])  # First week: [0, 1, 2, 3, 4, 5, 6]
```

#### `get_full_calendar(year: int, month: int) -> CalendarMonth`

**Main entry point** - Flask routes should call this function. Returns a complete calendar month with weather and holiday data.

**Data Structure:**

```python
CalendarMonth(
    year=2025,
    month=12,
    weeks=[CalendarWeek, ...],
    current_day=2  # Current day number if in this month, otherwise 0
)
```

**Usage Example:**

```python
from services.calendar_service import get_full_calendar

# Get calendar data
calendar_month = get_full_calendar(2025, 12)
calendar_month = calendar_month.to_dict()

# Access calendar matrix (list of weeks)
calendar_matrix = calendar_month['weeks']

# Get current day for highlighting
highlight_day = calendar_month['current_day']
```

## Design Decisions

### Why separate services from APIs?

1. **Separation of concerns:** HTTP requests vs. business logic
2. **Testability:** Easy to mock API calls and test transformations
3. **Reusability:** Multiple routes can use the same service functions
4. **Maintainability:** Changes to API structure don't affect business logic

### Why use dataclasses instead of dicts?

1. **Type safety:** IDE autocomplete and type checking
2. **Validation:** Dataclass structure enforces correct fields
3. **Documentation:** Clear contracts for data structures
4. **Serialization:** Easy `.to_dict()` methods for JSON responses

### Why cache holidays but not weather?

- **Holidays:** Static data, changes yearly, high reuse
- **Weather:** Dynamic data, must be fresh, low reuse (different hours/days)

## Usage

### Weather Service Usage

#### Get Current Weather

```python
from services.weather_service import get_current_weather

# Get current weather
current_weather = get_current_weather()
current_weather = current_weather.to_dict()

# Result: {
#   "temperature": 16,
#   "weather_code": {
#       "code": 2,
#       "icon": "partly_cloudy.svg",
#       "label": "Partly Cloudy"
#   }
# }
```

#### Get Hourly Forecast

```python
from services.weather_service import get_hourly_forecast_today

# Get hourly forecast
hourly_forecast = get_hourly_forecast_today()
hourly_forecast = [reading.to_dict() for reading in hourly_forecast]

# Result: [
#   {"temperature": 15, "weather_code": {"code": 1, "icon": "sunny.svg", "label": "Sunny"}},
#   {"temperature": 14, "weather_code": {"code": 2, "icon": "partly_cloudy.svg", "label": "Partly Cloudy"}},
#   ...
# ]
```

### Calendar Service Usage

```python
from services.calendar_service import get_full_calendar

# Get calendar data
calendar_month = get_full_calendar(2025, 12)
calendar_month = calendar_month.to_dict()

# Access calendar matrix (list of weeks)
calendar_matrix = calendar_month['weeks']
# Structure: [
#   [{day: 1, holidays: ["Christmas"], weather: {code: 3, icon: "cloudy.svg", label: "Cloudy"}}, ...],
#   [{day: 8, holidays: [], weather: {code: 1, icon: "sunny.svg", label: "Sunny"}}, ...],
#   ...
# ]

# Get current day for highlighting
highlight_day = calendar_month['current_day']

# Display month and year
year = calendar_month['year']
month = calendar_month['month']
```
