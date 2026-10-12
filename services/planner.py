"""Gathers what the suggestions need for one account: its places, its
settings, the forecast and its coming events, and makes the plans.

Suggestions are an extra on every page that shows them: if the places or
settings can't be read, pages carry on without them.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Set

from api.weather_api import LONDON
from database.db_event import events_between
from database.db_place import list_places
from database.db_settings import get_preferences
from models.api_models.suggestion import DayPlan, Preferences
from services import suggestion_service
from services.weather_service import get_day_outlooks

logger = logging.getLogger(__name__)


def london_now() -> datetime:
    """Now in London, without a timezone, like the forecast's times."""
    return datetime.now(LONDON).replace(tzinfo=None)


@dataclass
class AccountPlans:
    """Everything a page needs to show suggestions."""
    now: datetime
    prefs: Preferences
    places: List = field(default_factory=list)
    plans: List[DayPlan] = field(default_factory=list)

    @property
    def by_day(self) -> Dict[date, DayPlan]:
        return {p.day: p for p in self.plans}

    def plan_for(self, day: date) -> Optional[DayPlan]:
        return self.by_day.get(day)

    @property
    def today(self) -> Optional[DayPlan]:
        """The plan for the strip at the top of the home page."""
        return suggestion_service.today_pick(self.plans, self.prefs, self.now)

    @property
    def ahead(self) -> List[DayPlan]:
        return suggestion_service.good_days_ahead(
            self.plans, self.prefs, self.now)

    @property
    def great_days(self) -> Set[date]:
        """Days in the account's days with a great fit still ahead, for
        the marks in the month."""
        return {p.day for p in self.plans
                if p.has_great and self.prefs.includes(p.day)}

    def next_great(self, place_id: int):
        """The first great suggestion for a place in the account's days."""
        for plan in self.plans:
            if not self.prefs.includes(plan.day):
                continue
            found = plan.fit_for(place_id)
            if found and found.fit == "great":
                return found
        return None


def busy_by_day(events) -> Dict[date, Set]:
    """{day: place ids of that day's events (None for the others)}."""
    busy = defaultdict(set)
    for event in events:
        busy[event["start_time"].date()].add(event.get("place_id"))
    return busy


def account_plans(user_id: int, now: Optional[datetime] = None
                  ) -> AccountPlans:
    """The account's plans for every forecast day. Without places, a
    forecast or a database, the plans are simply empty."""
    now = now or london_now()
    try:
        prefs = get_preferences(user_id)
        places = list_places(user_id)
    except Exception:
        logger.exception("Could not read places or settings")
        return AccountPlans(now=now, prefs=Preferences())
    result = AccountPlans(now=now, prefs=prefs, places=places)
    if not places:
        return result
    outlooks = get_day_outlooks(now.date())
    if not outlooks:
        return result
    start = datetime.combine(now.date(), datetime.min.time())
    try:
        events = events_between(user_id, start,
                                start + timedelta(days=len(outlooks) + 1))
    except Exception:
        logger.exception("Could not read events for suggestions")
        events = []
    result.plans = suggestion_service.plan_days(
        outlooks, places, prefs, now, busy_by_day(events))
    return result
