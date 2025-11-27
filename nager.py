from datetime import date
import requests
from requests import Response
from typing import List, Dict, DefaultDict
from collections import defaultdict
from functools import lru_cache

@lru_cache(maxsize=10)
def get_holidays(year: int = 2024, country_code: str = "GB"):
    url: str = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"

    # Added timeout to prevent hanging indefinitely
    response: Response = requests.get(url, timeout=10)

    if response.status_code != 200:
        raise Exception(f"Error fetching holidays: {response.status_code}")
    
    holidays: DefaultDict[date, List[str]] = defaultdict(list)

    # holidays_data: List[Dict] = response.json()
    for item in response.json():
        date_obj = date.fromisoformat(item["date"])
        holidays[date_obj].append(item["localName"])
    return holidays
    # a dict with date type as key, list of holiday names as value
    # e.g., {date(2024, 1, 1): ['New Year\'s Day'], date(2024, 4, 1): ['Easter Monday'], ...}
    
    # O(1) lookup time for list of holidays on a specific date when we know the date string
    # O(n) time to loop through all the holidays in the list but holiday is rarely more than one per day

    # dict[date, list[str]], later if more field we can have holiday class and do dict[date, list[Holiday]]

    # serveal decision making points for returning structure:
    # 1. dict[date, list[Holiday]] vs dict[date, list[Dict]]
    # 2. dict[date, list[Holiday]] vs list[Dict]

    # In our code, the function that calls get_holidays uses the return and lookup holidays by date, so dict[date, list[Holiday]] is more suitable.