"""
Holiday service - Business logic for public holiday data.

This module provides functions for retrieving and organizing public holiday
information. It acts as an intermediary between the raw API data and the
application logic, transforming API responses into usable data structures.
"""

from functools import lru_cache
from typing import List, Dict
from collections import defaultdict
from datetime import date

from api.holiday_api import fetch_public_holidays
from models.api_models.holiday import Holiday


@lru_cache(maxsize=1)
def get_public_holidays(
    year: int = 2025, country_code: str = "GB"
) -> Dict[date, List[str]]:
    """
    Get all public holidays for a year, organized by date.

    Fetches holiday data from the Nager.Date API and transforms it into
    a dictionary for fast date-based lookups. Results are cached to avoid
    redundant API calls.

    Args:
        year: Year to fetch holidays for (default: 2025)
        country_code: ISO country code (default: "GB" for United Kingdom)

    Returns:
        Dictionary mapping date objects to lists of holiday names.
        Multiple holidays on the same day are stored in the list.

    Note:
        This function is cached with @lru_cache(maxsize=1) to avoid
        repeated API calls for the same year/country combination.
    """
    # Fetch raw holiday data from API
    data = fetch_public_holidays(year, country_code)

    # Transform raw API responses into Holiday objects
    holidays = [Holiday.from_api_response(item) for item in data]

    # Organize holidays by date for fast lookup
    # Use defaultdict to handle multiple holidays on the same day
    holidays_by_date = defaultdict(list)

    for holiday in holidays:
        holidays_by_date[holiday.date].append(holiday.local_name)

    # Convert defaultdict to regular dict before returning
    return dict(holidays_by_date)


def get_holidays_for_date(target_date: date, year: int = None) -> List[str]:
    """
    Get list of holiday names for a specific date.

    Convenience function to check if a particular date is a holiday and
    retrieve the holiday names if so.

    Args:
        target_date: Date to check for holidays
        year: Year to query (optional, defaults to target_date.year)

    Returns:
        List of holiday names for the given date. Empty list if no holidays.
    """
    # Use target date's year if not explicitly provided
    if year is None:
        year = target_date.year

    # Get all holidays for the year (cached)
    holidays_dict = get_public_holidays(year)

    # Return holidays for the specific date, or empty list if none
    return holidays_dict.get(target_date, [])
