from datetime import date, datetime
from typing import List
import calendar

from models.api_models.calendar import CalendarMonth, CalendarWeek, CalendarDay
from services.holiday_service import get_public_holidays
from services.weather_service import get_daily_forecast



def get_current_month_year() -> tuple[int, int]:
    now = datetime.now()
    return now.year, now.month


def get_current_day_if_matches(year: int, month: int) -> int:
    now = datetime.now()
    if now.year == year and now.month == month:
        return now.day
    return 0


def build_calendar_matrix(year: int, month: int) -> List[List[int]]:
    cal = calendar.Calendar(firstweekday=6) # Sunday as the first day of the week
    return cal.monthdayscalendar(year, month)


def get_calendar_with_holidays(year: int, month: int) -> CalendarMonth:
    matrix = build_calendar_matrix(year, month)

    holidays_dict = get_public_holidays(year)

    # Build calendar with holidays
    weeks = []
    for week in matrix:
        days = []
        for day in week:
            if day == 0:
                day = CalendarDay(day=0)
            else:
                date_obj = date(year, month, day)
                holiday_names = holidays_dict.get(date_obj, [])
                day = CalendarDay(day=day, holidays=holiday_names)
            
            days.append(day)
        weeks.append(CalendarWeek(days=days))
    
    current_day = get_current_day_if_matches(year, month)

    return CalendarMonth(year=year, month=month, weeks=weeks, current_day=current_day)


def get_calendar_with_weather(year: int, month: int) -> CalendarMonth:
    calendar_month = get_calendar_with_holidays(year, month)

    weather_dict = get_daily_forecast() # Dict[str, WeatherCode]

    for week in calendar_month.weeks:
        for day in week.days:
            if not day.is_empty:
                # Format date as YYYY-MM-DD
                date_str = f"{year:04d}-{month:02d}-{day.day:02d}"

                if date_str in weather_dict:
                    day.weather = weather_dict[date_str]

    return calendar_month


def get_full_calendar(year: int, month: int) -> CalendarMonth:

    return get_calendar_with_weather(year, month)