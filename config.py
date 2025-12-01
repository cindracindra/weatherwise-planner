class Config:
    # Location
    LONDON_LAT = 51.5074
    LONDON_LON = -0.1278
    TIMEZONE = "Europe/London"

    # API Endpoints
    OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
    NAGER_BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"

    # Defaults
    DEFAULT_COUNTRY_CODE = "GB"
    DEFAULT_HOLIDAY_YEAR = 2025

    # PATHS
    WEATHER_CODES_ICON_PATH = "static/data/code_icon.json"

    # Timeout settings
    API_TIMEOUT = 10  # seconds