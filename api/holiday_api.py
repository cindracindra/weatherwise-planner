import requests
from requests import Response
from typing import Any, Dict, List
from config import Config

class HolidayAPIError(Exception):
    """Raised when holiday API requests fail."""
    pass

def _make_request(year: int, country_code: str) -> Dict[str, Any]:
    try:
        response: Response = requests.get(
            f"{Config.NAGER_DATE_BASE_URL}/{year}/{country_code}", 
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HolidayAPIError(f"Holiday API request failed: {e}")

def fetch_public_holidays(year: int = 2025, country_code: str = Config.DEFAULT_COUNTRY_CODE) -> Dict[str, Any]:

    return _make_request(year, country_code)