from functools import lru_cache
from typing import List, Dict
from collections import defaultdict
from datetime import date

from api.holiday_api import fetch_public_holidays
from models.api_models.holiday import Holiday


@lru_cache(maxsize=1)
def get_public_holidays(year: int = 2025, country_code: str = "GB") -> Dict[date, List[str]]:
    data = fetch_public_holidays(year, country_code)

    holidays = [Holiday.from_api_response(item) for item in data]

    holidays_by_date = defaultdict(list)

    for holiday in holidays:
        holidays_by_date[holiday.date].append(holiday.local_name)

    return dict(holidays_by_date)


def get_holidays_for_date(target_date: date, year: int = None) -> List[str]:
    if year is None:
        year = target_date.year

    holidays_dict = get_public_holidays(year)

    return holidays_dict.get(target_date, [])