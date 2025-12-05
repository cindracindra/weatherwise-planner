"""
Calendar data models for representing monthly calendars.

This module provides dataclasses for building calendar views that combine
dates, holidays, and weather information. Used to generate monthly calendar
displays in the application.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from models.api_models.weather import WeatherCode


@dataclass
class CalendarDay:
    """
    Represents a single day cell in a calendar grid.

    Attributes:
        day: Day of month (0 for empty cells, 1-31 for actual days)
        holidays: List of holiday names for this day (empty if none)
        weather: Weather forecast for this day (None if not available)

    Properties:
        is_empty: True if this is an empty calendar cell (day == 0)
        is_holiday: True if this day has any holidays
    """
    day: int
    holidays: List[str] = field(default_factory=list)
    weather: Optional[WeatherCode] = None

    @property
    def is_empty(self) -> bool:
        """
        Check if this is an empty calendar cell.

        Empty cells appear at the beginning or end of months when the
        month doesn't start on Sunday or end on Saturday.
        """
        return self.day == 0

    @property
    def is_holiday(self) -> bool:
        """
        Check if this day has any holidays.

        Returns:
            True if holidays list is not empty, False otherwise
        """
        return len(self.holidays) > 0

    def to_dict(self) -> dict:
        """
        Convert CalendarDay to JSON-serializable dictionary.
        """
        return {
            "day": self.day,
            "holidays": self.holidays,
            "weather": self.weather.to_dict() if self.weather else None
        }


@dataclass
class CalendarWeek:
    """
    Represents a week in the calendar (always 7 days).

    Calendar grids always display complete weeks for visual consistency,
    regardless of which day the month starts or ends on.

    Attributes:
        days: List of exactly 7 CalendarDay objects (Sunday to Saturday)

    Raises:
        ValueError: If days list doesn't contain exactly 7 elements
    """
    days: List[CalendarDay]

    def __post_init__(self):
        """
        Validate that the week contains exactly 7 days.

        This validation runs automatically after object creation to ensure
        calendar grid integrity.

        Raises:
            ValueError: If days list length is not 7
        """
        if len(self.days) != 7:
            raise ValueError("A week must contain exactly 7 days.")

    def to_dict(self) -> List[dict]:
        """
        Convert CalendarWeek to list of day dictionaries.

        Returns:
            List of 7 dictionaries, one for each day in the week
        """
        return [day.to_dict() for day in self.days]


@dataclass
class CalendarMonth:
    """
    Represents a complete month calendar with weeks, holidays, and weather.

    A calendar month consists of 4-6 complete weeks (Sunday-Saturday),
    depending on which day the month starts and how many days it has.

    Attributes:
        year: Year (e.g., 2025)
        month: Month number (1-12)
        weeks: List of CalendarWeek objects (typically 4-6 weeks)
        current_day: Day to highlight (0 if not current month, 1-31 otherwise)
    """
    year: int
    month: int
    weeks: List[CalendarWeek]
    current_day: int = 0  # Day to highlight for today (0 if not current month)

    def to_dict(self) -> dict:
        """
        Convert CalendarMonth to JSON-serializable dictionary.

        Returns:
            Dictionary with 'year', 'month', 'weeks', and 'current_day' keys.
            The 'weeks' value is a list of lists (week -> days).

        Note:
            This structure is designed for easy consumption by frontend
            JavaScript code that renders the calendar grid.
        """
        return {
            "year": self.year,
            "month": self.month,
            "weeks": [weeks.to_dict() for weeks in self.weeks],
            "current_day": self.current_day
        }
