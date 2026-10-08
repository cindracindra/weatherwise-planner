# Weather, holidays and the calendar

How the app gets London's weather and UK public holidays and turns them into the calendar. Three layers, each only talking to the one below:

```
routes ──▶ services/      business logic, caching, shaping data for pages
             ──▶ api/      raw HTTP calls to Open-Meteo and Nager.Date
             ──▶ models/api_models/   small dataclasses passed between them
```

Settings (location, time zone, API URLs, timeout) live in `config.py`.

## `api/`: talking to the outside services

| File | Calls | Functions |
|---|---|---|
| `weather_api.py` | [Open-Meteo](https://open-meteo.com) | `fetch_current_weather()`, `fetch_hourly_forecast_today()` (temperature, weather code and chance of rain for each hour), `fetch_daily_forecast()` (16 days of weather codes) |
| `holiday_api.py` | [Nager.Date](https://date.nager.at) | `fetch_public_holidays(year, country_code)` |

Both return the parsed JSON. If Open-Meteo times out or fails, the weather functions log it and return empty data, so the page still renders without a forecast. A failed holiday request raises `HolidayAPIError`.

## `services/`: what the routes call

| Function | Returns | Cached |
|---|---|---|
| `weather_service.get_current_weather()` | `WeatherReading` for now | 30 min |
| `weather_service.get_hourly_forecast_today()` | 24 `WeatherReading`s, one per hour, each with `rain_chance` | 1 hour |
| `weather_service.get_daily_forecast()` | `{"YYYY-MM-DD": WeatherCode}` for 16 days; days with no forecast are left out | 1 hour |
| `holiday_service.get_public_holidays(year)` | `{date: [holiday names]}` | per year |
| `calendar_service.get_full_calendar(year, month)` | `CalendarMonth`: weeks of days, each with its holidays and forecast | |
| `datetime_service.get_today_detail()` | Today in London: day, month, year, hour, names | |

Times and "today" are always London time (`Config.TIMEZONE`), matching the forecast.

## `models/api_models/`: the data passed around

| Class | Fields |
|---|---|
| `WeatherCode` | `code` (WMO weather code), `label` (e.g. "Drizzle"), `icon` |
| `WeatherReading` | `temperature` (rounded °C), `weather_code`, `rain_chance` (0-100) |
| `Holiday` | one holiday from Nager.Date |
| `CalendarDay` / `CalendarWeek` / `CalendarMonth` | the month grid: `day` (0 for blank cells), `holidays`, `weather` |

Each has `to_dict()` for templates and JSON.

Labels come from `static/data/code_icon.json`, which maps each WMO code to a label. The pages draw weather with [Phosphor](https://phosphoricons.com) icons chosen from the code (`templates/_macros.html`, `weather_glyph`); the `icon` file names in that JSON are left over from an earlier design and aren't displayed.
