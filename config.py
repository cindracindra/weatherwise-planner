class Config:
    # Location
    LONDON_LAT = 51.5074
    LONDON_LON = -0.1278
    TIMEZONE = "Europe/London"

    # API Endpoints
    OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
    # Backup when Open-Meteo refuses (e.g. 429 on a shared hosting address)
    MET_NORWAY_URL = (
        "https://api.met.no/weatherapi/locationforecast/2.0/complete"
    )
    NAGER_DATE_BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"

    # Defaults
    DEFAULT_COUNTRY_CODE = "GB"
    DEFAULT_HOLIDAY_YEAR = 2025

    # PATHS
    WEATHER_CODES_ICON_PATH = "static/data/code_icon.json"

    # Weather services ask apps to identify themselves; MET Norway
    # requires a name and a contact (a website is accepted)
    USER_AGENT = (
        "WeatherWisePlanner/1.0 "
        "(+https://github.com/cindracindra/weatherwise-planner)"
    )

    # Timeout settings
    API_TIMEOUT = 10  # seconds
