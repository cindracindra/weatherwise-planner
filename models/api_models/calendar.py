from dataclasses import dataclass, field
from typing import List, Optional
from models.api_models.weather import WeatherCode


@dataclass
class CalendarDay:
    day: int
    holidays: List[str] = field(default_factory=list)
    weather: Optional[WeatherCode] = None

    @property
    def is_empty(self) -> bool:
        return self.day == 0

    @property
    def is_holiday(self) -> bool:
        return len(self.holidays) > 0

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "holidays": self.holidays,
            "weather": self.weather.to_dict() if self.weather else None
        }


@dataclass
class CalendarWeek:
    days: List[CalendarDay]

    def __post_init__(self):
        if len(self.days) != 7:
            raise ValueError("A week must contain exactly 7 days.")

    def to_dict(self) -> List[dict]:
        return [day.to_dict() for day in self.days]


@dataclass
class CalendarMonth:
    year: int
    month: int
    weeks: List[CalendarWeek]
    current_day: int = 0  # day to highlight for today (0 if not current month)

    def to_dict(self) -> List[List[dict]]:
        return {
            "year": self.year,
            "month": self.month,
            "weeks": [weeks.to_dict() for weeks in self.weeks],
            "current_day": self.current_day
        }
