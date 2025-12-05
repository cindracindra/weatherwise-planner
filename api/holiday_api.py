import requests
from requests import Response
from typing import Any, Dict
from config import Config
from datetime import datetime


class HolidayAPIError(Exception):
    """Custom exception raised when a public holiday API request fails."""
    pass


def _make_request(year: int, country_code: str) -> Dict[str, Any]:
    """
    Internal private helper function to send a GET request to the Nager.Date API.

    Args:
        year: The year for which public holidays should be fetched.
        country_code: ISO country code (e.g., "GB", "US") used by the API.

    Returns:
        List of holiday dictionaries from the API. Each dictionary contains:
        - date (str): Holiday date in ISO format (YYYY-MM-DD)
        - localName (str): Holiday name in local language
        - name (str): Holiday name in English
        - countryCode (str): Country code
        - fixed (bool): Whether the holiday is on a fixed date
        - global (bool): Whether it's a nationwide holiday
        - counties (List[str] | None): List of counties if applicable
        - launchYear (int | None): Year the holiday was launched
        - types (List[str]): Types of holiday (e.g., "Public", "Bank

    Raises:
        HolidayAPIError: If the HTTP request fails or returns an error status.

    Example:
        >>> _make_request(2025, 'GB')
        [
            {
                'date': '2025-01-01',
                'localName': "New Year's Day",
                'name': "New Year's Day",
                'countryCode': 'GB',
                'fixed': True,
                'global': True,
                "counties": None,
                "launchYear": None,
                "types": ["Public"]
            },
            ...
        ]
    """
    try:
        # Make GET request with timeout from config
        response: Response = requests.get(
            f"{Config.NAGER_DATE_BASE_URL}/{year}/{country_code}", timeout=Config.API_REQUEST_TIMEOUT
        )

        # Raise exception for HTTP errors status codes
        response.raise_for_status()

        return response.json()
    except requests.RequestException as e:
        # Wrap all requests exceptions in our custom exception
        raise HolidayAPIError(f"Holiday API request failed: {e}")


def fetch_public_holidays(year: int | None = None,
                          country_code: str = Config.DEFAULT_COUNTRY_CODE
                          ) -> Dict[str, Any]:
    """
    Fetch public holidays for a specific year and country.
    
    This is the main public function for fetching holiday data from the
    Nager.Date API. It returns raw JSON data that should be processed by
    the service layer.
    
    Args:
        year: Year to fetch holidays for. Defaults to current year if None.
        country_code: ISO two-letter country code (default from Config.DEFAULT_COUNTRY_CODE).
        
    Returns:
        List of dictionaries containing raw holiday data from the API.
        See _make_request() for the structure of each dictionary.
        
    Raises:
        HolidayAPIError: If the API request fails
        
    Note:
        This function returns raw API data. For structured Holiday objects,
        use the holiday_service.get_public_holidays() function instead.
    """
    if year is None:
        year = datetime.now().year
    return _make_request(year, country_code)
