# Services Layer Documentation

The services layer contains business logic that transforms raw API data into application-ready data structures. Services orchestrate data from multiple sources and apply business rules, acting as an intermediary between the API layer and Flask routes.

## Architecture Overview

```
┌─────────────────┐
│   Flask Routes  │  (app.py)
│   (app.py)      │
└────────┬────────┘
         │ calls
         ▼
┌─────────────────┐
│  Service Layer  │  (services/)
│                 │  - Business logic
│                 │  - Data transformation
│                 │  - Multi-source orchestration
└────────┬────────┘
         │ calls
         ▼
┌─────────────────┐
│   API Layer     │  (api/)
│                 │  - Raw HTTP requests
│                 │  - JSON parsing
└─────────────────┘
```

## Service Files

### 1. weather_service.py

**Purpose:** Transforms raw weather API data into structured WeatherReading objects with human-readable labels and icons.

**Key Functions:**

#### `get_current_weather() -> WeatherReading`

Fetches current weather conditions and adds weather code information (icon and label).

#### `get_hourly_forecast_today() -> List[WeatherReading]`

Fetches 24-hour hourly forecast and processes each hour into WeatherReading objects.

#### `get_daily_forecast() -> Dict[str, WeatherCode]`

Fetches 16-day daily forecast as a dictionary mapping ISO date strings to WeatherCode objects. Used internally by calendar_service.

**Data Flow:**

```
weather_api.fetch_current_weather()
    → Returns: {"current": {"temperature_2m": 15.3, "weather_code": 61}}
    ↓
weather_service.get_current_weather()
    → Rounds temperature: 15.3 → 15
    → Converts code to info: 61 → ("rain.svg", "Rain")
    → Returns: WeatherReading(temperature=15, weather_code=WeatherCode(...))
    ↓
Flask route (app.py)
    → Serializes to JSON: {"temperature": 15, "weather_code": {"code": 61, ...}}
```

---

### 2. holiday_service.py

**Purpose:** Transforms raw holiday API data into organized, date-indexed structures for fast lookups.

**Key Functions:**

#### `get_public_holidays(year: int = 2025, country_code: str = "GB") -> Dict[date, List[str]]`

Fetches all public holidays for a year and organizes them by date for efficient lookups.

**Features:**

- Caches results with `@lru_cache(maxsize=1)` to avoid redundant API calls
- Handles multiple holidays on the same day
- Returns regular dict (not defaultdict) for consistent behavior

#### `get_holidays_for_date(target_date: date, year: int = None) -> List[str]`

Convenience function to check if a specific date is a holiday.

---

### 3. calendar_service.py

**Purpose:** Orchestrates calendar generation by combining date matrices, holidays, and weather forecasts into rich CalendarMonth objects.

**Key Functions:**

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
# Sunday is 0 (empty), Monday-Saturday are 1-6
```

#### `get_calendar_with_holidays(year: int, month: int) -> CalendarMonth`

Intermediate function that builds a calendar with holiday information (but no weather).

#### `get_calendar_with_weather(year: int, month: int) -> CalendarMonth`

Complete calendar with both holidays and weather forecasts.

#### `get_full_calendar(year: int, month: int) -> CalendarMonth`

**Main entry point** - Flask routes should call this function.

---

## Common Patterns

### Service Layer Responsibilities

Services handle:

- **Data transformation:** Converting API responses to domain models
- **Business logic:** Rounding temperatures, formatting dates, combining data
- **Multi-source orchestration:** Combining holidays + weather + calendar matrix
- **Caching:** Using `@lru_cache` to avoid redundant API calls

Services do NOT:

- Make HTTP requests directly (that's the API layer's job)
- Handle Flask request/response logic (that's the route's job)
- Contain UI logic or HTML generation

---

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

---

## Related Documentation

- **API Layer:** See [api/README.md](../api/README.md) for raw API client details
- **Models:** See [models/api_models/README.md](../models/api_models/README.md) for data structure documentation
- **Utils:** See `utils/converters.py` for shared transformation functions

---

## Summary

The services layer is the **business logic hub** of the application. It:

1. **Transforms** raw API data into rich domain models
2. **Orchestrates** multiple data sources (holidays + weather + calendar)
3. **Applies** business rules (rounding, formatting, combining)
4. **Caches** where appropriate to improve performance
5. **Provides** clean, type-safe interfaces for Flask routes

Flask routes should always call service functions, never API functions directly.
