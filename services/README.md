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
| `weather_api.py` | [Open-Meteo](https://open-meteo.com), backup [MET Norway](https://api.met.no) | `fetch_forecast()`: current, hourly and 16-day forecast. Tries `fetch_open_meteo()` (one request for everything); if that fails, `fetch_met_norway()` |
| `holiday_api.py` | [Nager.Date](https://date.nager.at) | `fetch_public_holidays(year, country_code)` |
| `geocode_api.py` | [Nominatim](https://nominatim.org) (OpenStreetMap) | `search(query)`: up to 5 addresses in Greater London for a place's pin |

`fetch_forecast()` returns the same "forecast bundle" from either source: `current`, `hourly` (London times, each with whether it is day), `daily` (`{"YYYY-MM-DD": code}`) and `days` (each day's high, low, highest chance of rain and strongest wind), all with WMO weather codes. MET Norway's symbols (`lightrainshowers_day`, ...) are converted to WMO codes, its UTC times to London time, and a day's weather is the forecast nearest midday. It has no chance of rain for the UK, so `rain_chance` is empty then and the page leaves the rain sentence out.

Why a backup: Open-Meteo's free tier limits requests per IP address, and hosts like Render share addresses between many apps, so it can answer `429 Too Many Requests` for reasons that have nothing to do with this app. Every request carries a `User-Agent` naming the app (`Config.USER_AGENT`), which MET Norway requires.

Any failure (timeout, connection, HTTP error) becomes `WeatherAPIError`; `fetch_forecast()` raises it only if both sources fail. A failed holiday request raises `HolidayAPIError`.

## `services/`: what the routes call

| Function | Returns |
|---|---|
| `weather_service.get_current_weather()` | `WeatherReading` for now |
| `weather_service.get_hourly_forecast_today()` | 24 `WeatherReading`s for today, one per hour; hours the source doesn't cover have no values |
| `weather_service.get_daily_forecast()` | `{"YYYY-MM-DD": WeatherCode}`; days with no usable forecast are left out |
| `weather_service.get_day_outlooks()` | A `DayOutlook` for each forecast day from today: its weather, high, low, rain chance, wind and hours |
| `planner.account_plans(user_id)` | `AccountPlans`: the account's places, settings and a `DayPlan` per forecast day; empty, never an error, if anything is missing |
| `holiday_service.get_public_holidays(year)` | `{date: [holiday names]}`, cached per year |
| `calendar_service.get_full_calendar(year, month)` | `CalendarMonth`: weeks of days, each with its holidays and forecast |
| `datetime_service.get_today_detail()` | Today in London: day, month, year, hour, names |

The three weather functions share **one forecast** (`get_forecast()`):

- a forecast is reused for **30 minutes**, so a page view normally makes no weather request at all;
- if a refresh fails, the **last good forecast keeps showing for up to 12 hours**;
- after a failure the app **waits a minute** before asking again, rather than on every page view.

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

## Suggestions (`suggestion_service.py`)

Matches places against the forecast, with no database or web code, so it is tested on its own (`tests/unit/test_suggestion_service.py`).

- `classify(code, rain_chance)`: the kind of weather (sunny, cloudy, rainy, severe).
- `base_fit(place, kind)`: great, okay or poor (see "How suggestions work" in the main README).
- `best_time(place, day, start_hour, end_hour)`: slides a visit of the place's length through the hours, hour by hour, and keeps the best fit, then the driest; temperature, wind and darkness are taken into account. `judge_day` judges the whole day when there are no hours.
- `plan_day` / `plan_days`: every place for each day, best first, honouring the settings window, what is still ahead today, and the account's events that day.
- `today_pick`: what today (or, from the evening, tomorrow) is good for. A day's picks are its great fits only.

`planner.py` gathers the inputs for an account (places, settings, forecast, the next 16 days' events) and calls it. Address search is paced to one request a second and cached for a day, as Nominatim's usage policy asks; it only runs when someone presses Search.
