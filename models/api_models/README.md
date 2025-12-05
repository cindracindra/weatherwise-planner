# API Models

This directory contains data models (dataclasses) for external API responses. These models provide type-safe structures for data returned from third-party APIs.

## Overview

API models serve as:

- **Data Transfer Objects (DTOs)** - Structured representations of API responses
- **Type safety** - Ensure correct data types throughout the application
- **Serialization** - Convert between Python objects and JSON dictionaries
- **Documentation** - Self-documenting data structures with clear field types

**Important:** These models represent external API data, NOT database tables.

---

## Weather Models (`weather.py`)

Data models for weather information from the Open-Meteo API.

### `WeatherCode`

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

# Create a weather code
wc = WeatherCode(
    code=61,
    icon="rain.svg",
    label="Rain"
)

# Convert to dictionary (for JSON responses)
wc_dict = wc.to_dict()
# {'code': 61, 'icon': 'rain.svg', 'label': 'Rain'}
```

---

### `WeatherReading`

Represents a single weather measurement with temperature and conditions.

**Fields:**

- `temperature: Optional[int]` - Temperature in Celsius (rounded)
- `weather_code: WeatherCode` - Weather condition details

**Methods:**

- `to_dict() -> dict` - Converts to JSON-serializable dictionary

**Example:**

```python
from models.api_models.weather import WeatherCode, WeatherReading

# Create a weather reading
wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
reading = WeatherReading(
    temperature=15,
    weather_code=wc
)

# Convert to dictionary
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

**Use Cases:**

- Current weather conditions
- Hourly weather forecast (list of WeatherReadings)
- Temperature display in UI

---

## Holiday Models (`holiday.py`)

Data models for public holiday information from the Nager.Date API.

### `Holiday`

Represents a public holiday with its date and name.

**Fields:**

- `date: date` - Holiday date (Python datetime.date object)
- `local_name: str` - Holiday name in local language

**Class Methods:**

- `from_api_response(cls, data: dict) -> Holiday` - Creates Holiday from raw API data

**Instance Methods:**

- `to_dict() -> dict` - Converts to JSON-serializable dictionary

---

## Calendar Models (`calendar.py`)

Data models for calendar representation, combining dates, holidays, and weather.

### `CalendarDay`

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

# Holiday with weather
wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
holiday = CalendarDay(
    day=25,
    holidays=["Christmas Day"],
    weather=wc
)

print(holiday.is_holiday)  # True
print(holiday.to_dict())
# {
#     'day': 25,
#     'holidays': ['Christmas Day'],
#     'weather': {'code': 61, 'icon': 'rain.svg', 'label': 'Rain'}
# }
```

**Why day can be 0:**
Calendar months don't always start on Sunday. Empty cells at the beginning/end of the month are represented with `day=0`.

---

### `CalendarWeek`

Represents a week in the calendar (always 7 days).

**Fields:**

- `days: List[CalendarDay]` - Exactly 7 CalendarDay objects

**Validation:**

- Raises `ValueError` if days list doesn't contain exactly 7 elements

**Methods:**

- `to_dict() -> List[dict]` - Converts to list of day dictionaries

**Why exactly 7 days:**
Calendar grids always display full weeks (Sunday-Saturday) for visual consistency.

---

### `CalendarMonth`

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

# Build a simple month (1 week for demo)
days = [CalendarDay(day=i) for i in range(7)]
week = CalendarWeek(days=days)

month = CalendarMonth(
    year=2025,
    month=12,
    weeks=[week],
    current_day=15  # Highlight the 15th
)

# Convert to dictionary (for Flask JSON response)
month_dict = month.to_dict()
# {
#     'year': 2025,
#     'month': 12,
#     'weeks': [
#         [{'day': 0, 'holidays': [], 'weather': None}, ...]
#     ],
#     'current_day': 15
# }
```

**Typical Structure:**

- **4 weeks:** February in non-leap year starting on Sunday
- **5 weeks:** Most common (e.g., December 2025)
- **6 weeks:** When month spans parts of 6 different weeks

---

## Model Relationships

```
CalendarMonth
    └─ weeks: List[CalendarWeek]
            └─ days: List[CalendarDay]
                    ├─ holidays: List[str]
                    └─ weather: Optional[WeatherCode]

WeatherReading
    └─ weather_code: WeatherCode

Holiday
    (standalone - converted to list of strings in CalendarDay)
```

---

## Related Documentation

- **API Layer:** `../../api/README.md` - Raw API clients
- **Service Layer:** `../../services/` - Business logic using these models
- **Tests:** `../../tests/unit/test_models.py` - Model tests
- **Config:** `../../config.py` - Application configuration
