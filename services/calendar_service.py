"""
Calendar service - Business logic for calendar generation.

This module provides functions for building monthly calendar
grids that combine date information with holidays and weather
data. It orchestrates data from holiday_service and weather_service
to create rich CalendarMonth objects for
display in the application.

The calendar generation follows a multi-layer approach:
1. Build calendar matrix (grid of days)
2. Add holiday information to each day
3. Add weather forecast to each day
4. Mark the current day for highlighting

This service layer is the primary interface for Flask routes that need
calendar data with integrated holidays and weather information.
"""

from datetime import date, datetime
from typing import List
import calendar
from models.api_models.calendar import CalendarMonth, CalendarWeek, CalendarDay
from services.holiday_service import get_public_holidays
from services.weather_service import get_daily_forecast


def get_current_month_year() -> tuple[int, int]:
    """
    Get the current month and year.

    Returns:
        Tuple of (year, month) for the current date.
        Year is a 4-digit integer, month is 1-12.
    """
    now = datetime.now()
    return now.year, now.month


def get_current_day_if_matches(year: int, month: int) -> int:
    """
    Get the current day number if it matches the given year and month.

    This function is used to determine which day to highlight in the calendar
    when displaying the current month.

    Args:
        year: Year to check (4-digit integer)
        month: Month to check (1-12)

    Returns:
        Current day of month (1-31) if year and month match today's date,
        otherwise 0 to indicate no highlighting needed.
    """
    now = datetime.now()
    if now.year == year and now.month == month:
        return now.day
    return 0


def build_calendar_matrix(year: int, month: int) -> List[List[int]]:
    """
    Build a calendar matrix (grid of days) for a specific month.

    Creates a 2D list representing the calendar layout with weeks as rows
    and days as columns. The calendar starts on Sunday and includes empty
    cells (represented as 0) for days outside the current month.

    Args:
        year: Year for the calendar (4-digit integer)
        month: Month number (1-12)

    Returns:
        List of weeks, where each week is a list of 7 integers.
        Valid day numbers are 1-31, and 0 represents empty cells.
    """
    cal = calendar.Calendar(firstweekday=6)  # Week starts on Sunday
    return cal.monthdayscalendar(year, month)


def get_calendar_with_holidays(year: int, month: int) -> CalendarMonth:
    """
    Build a calendar with holiday information for each day.

    Creates a CalendarMonth object with all days populated with their
    corresponding holiday data. Days with no holidays have empty holiday lists.
    The current day is also marked for highlighting if displaying
    current month.

    Args:
        year: Year for the calendar (4-digit integer)
        month: Month number (1-12)

    Returns:
        CalendarMonth object with weeks containing CalendarDay objects.
        Each CalendarDay includes:
        - day: Day number (0 for empty cells, 1-31 for actual days)
        - holidays: List of holiday names (empty if no holidays)
        - weather: None (weather not added at this stage)

    Note:
        This is an intermediate function in the calendar generation pipeline.
        It's typically called by get_calendar_with_weather() rather than
        directly by Flask routes.
    """
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

    return CalendarMonth(
        year=year, month=month, weeks=weeks, current_day=current_day
    )


def get_calendar_with_weather(year: int, month: int) -> CalendarMonth:
    """
    Build a complete calendar with both holidays and weather forecasts.

    Args:
        year: Year for the calendar (4-digit integer)
        month: Month number (1-12)

    Returns:
        CalendarMonth object with complete data for each day:
        - day: Day number (0 for empty cells, 1-31 for actual days)
        - holidays: List of holiday names (empty if no holidays)
        - weather: WeatherCode object (None if forecast not available)
        - current_day: Marked for highlighting if displaying current month

    Note:
        This function is the main pipeline for calendar generation:
        1. Builds calendar matrix
        2. Adds holidays via get_calendar_with_holidays()
        3. Adds weather forecasts from get_daily_forecast()

        Weather data is matched to days using ISO date format (YYYY-MM-DD).
        Days without available weather forecasts will have weather=None.
    """
    calendar_month = get_calendar_with_holidays(year, month)

    weather_dict = get_daily_forecast()  # Dict[str, WeatherCode]

    for week in calendar_month.weeks:
        for day in week.days:
            if not day.is_empty:
                # Format date as YYYY-MM-DD
                date_str = f"{year:04d}-{month:02d}-{day.day:02d}"

                if date_str in weather_dict:
                    day.weather = weather_dict[date_str]

    return calendar_month


# Main functions to be used externally by app.py
def get_full_calendar(year: int, month: int) -> CalendarMonth:
    return get_calendar_with_weather(year, month)
