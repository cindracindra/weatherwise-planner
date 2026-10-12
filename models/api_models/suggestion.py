"""What the suggestions are made of: preferences, fits and day plans."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, List, Optional

from models.api_models.weather import DayOutlook

# How well a place suits some weather, best first
GREAT, OKAY, POOR = "great", "okay", "poor"
FIT_ORDER = {GREAT: 0, OKAY: 1, POOR: 2}
# Shown beside the colour wherever a fit appears, so colour is never the
# only signal
FIT_LABELS = {GREAT: "Great", OKAY: "Okay", POOR: "Not ideal"}
FIT_ICONS = {GREAT: "check-circle", OKAY: "minus-circle", POOR: "x-circle"}

# What kind of weather a day (or an hour) is
SUNNY, CLOUDY, RAINY, SEVERE = "sunny", "cloudy", "rainy", "severe"
KIND_LABELS = {SUNNY: "Sunny", CLOUDY: "Dry, cloudy", RAINY: "Rain likely",
               SEVERE: "Snow or storms"}


@dataclass
class Preferences:
    """How an account wants suggestions (see UserSettings for storage).

    days lists the weekdays to suggest for as digits, Monday 0 to Sunday 6.
    The hours are the window searched for good weather, start inclusive
    and end exclusive."""
    days: str = "0123456"
    weekday_start: int = 18
    weekday_end: int = 21
    weekend_start: int = 9
    weekend_end: int = 18
    skip_busy_days: bool = False
    show_today: bool = True

    def includes(self, day: date) -> bool:
        return str(day.weekday()) in self.days

    def window(self, day: date) -> tuple[int, int]:
        if day.weekday() >= 5:
            return self.weekend_start, self.weekend_end
        return self.weekday_start, self.weekday_end


@dataclass
class Suggestion:
    """One place on one day: how well it fits, when, and why."""
    place: Any                   # a Place, or anything with its fields
    day: date
    fit: str                     # GREAT, OKAY or POOR
    kind: str                    # the weather in the chosen window
    start: datetime
    end: datetime
    temperature: Optional[int]   # warmest in the window, or the day's high
    reasons: List[str] = field(default_factory=list)
    dark: bool = False           # some of the window is after dark

    @property
    def fit_label(self) -> str:
        return FIT_LABELS[self.fit]

    @property
    def fit_icon(self) -> str:
        return FIT_ICONS[self.fit]

    @property
    def kind_label(self) -> str:
        """The weather in words; a clear night is 'Clear', not 'Sunny'."""
        if self.kind == SUNNY and self.dark:
            return "Clear"
        return KIND_LABELS[self.kind]

    @property
    def summary(self) -> str:
        """'Sunny 11:00-13:00, 22°' plus any reason it was marked down."""
        text = (f"{self.kind_label} "
                f"{self.start:%H:%M}-{self.end:%H:%M}")
        if self.temperature is not None:
            text += f", {self.temperature}°"
        if self.reasons:
            text += "; " + "; ".join(self.reasons)
        return text


@dataclass
class DayPlan:
    """A forecast day and the places that suit it."""
    outlook: DayOutlook
    kind: str                    # the day as a whole
    busy: bool                   # the day already has events
    # Every place judged, best first
    suggestions: List[Suggestion] = field(default_factory=list)
    # The weather in the account's hours that day, which suggestions are
    # judged on and can differ from the day as a whole
    window_start: Optional[int] = None
    window_end: Optional[int] = None
    window_kind: Optional[str] = None
    dark_from: Optional[int] = None  # first hour in the window after dark

    @property
    def window_label(self) -> Optional[str]:
        if self.window_kind is None:
            return None
        if self.window_kind == SUNNY and self.dark_from == self.window_start:
            return "Clear"
        return KIND_LABELS[self.window_kind]

    @property
    def day(self) -> date:
        return self.outlook.day

    @property
    def picks(self) -> List[Suggestion]:
        """What to put forward: the great fits only."""
        return [s for s in self.suggestions if s.fit == GREAT]

    @property
    def has_great(self) -> bool:
        return any(s.fit == GREAT for s in self.suggestions)

    def fit_for(self, place_id: int) -> Optional[Suggestion]:
        for s in self.suggestions:
            if getattr(s.place, "id", None) == place_id:
                return s
        return None
