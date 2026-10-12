"""Suggestion settings: one optional row per account."""

from dataclasses import asdict
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.engine import engine
from models.api_models.suggestion import Preferences
from models.db_models.settings import UserSettings

# Presets the settings page offers for "Days to suggest"
DAY_PRESETS = {"every": "0123456", "weekends": "56"}
FIELDS = ("weekday_start", "weekday_end", "weekend_start", "weekend_end")


def _to_preferences(row: UserSettings) -> Preferences:
    return Preferences(
        days=row.suggest_days,
        weekday_start=row.weekday_start, weekday_end=row.weekday_end,
        weekend_start=row.weekend_start, weekend_end=row.weekend_end,
        skip_busy_days=row.skip_busy_days, show_today=row.show_today,
    )


def get_preferences(user_id: int) -> Preferences:
    """The account's settings, or the defaults if it has never saved any.
    Raises on a database failure."""
    with Session(engine) as session:
        row = session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        ).scalar_one_or_none()
        return _to_preferences(row) if row else Preferences()


def clean_preferences(form: Dict[str, Any]) -> Preferences:
    """Preferences from the settings form, checked. Raises ValueError with
    a message fit to show the person.

    days is a preset ("every", "weekends") or "custom" with the chosen
    weekdays as day_0 .. day_6 tick boxes."""
    preset = form.get("days", "every")
    if preset in DAY_PRESETS:
        days = DAY_PRESETS[preset]
    elif preset == "custom":
        days = "".join(str(d) for d in range(7) if form.get(f"day_{d}"))
        if not days:
            raise ValueError("Choose at least one day for suggestions.")
    else:
        raise ValueError("Choose which days to get suggestions for.")

    hours = {}
    for key in FIELDS:
        try:
            hours[key] = int(form.get(key, ""))
        except (TypeError, ValueError):
            raise ValueError("Choose a start and end time for each window.")
        if not 0 <= hours[key] <= 24:
            raise ValueError("Times must be between 00:00 and 24:00.")
    if hours["weekday_start"] >= hours["weekday_end"]:
        raise ValueError("On weekdays, the end must be after the start.")
    if hours["weekend_start"] >= hours["weekend_end"]:
        raise ValueError("At weekends, the end must be after the start.")

    return Preferences(
        days=days, **hours,
        skip_busy_days=bool(form.get("skip_busy_days")),
        show_today=bool(form.get("show_today")),
    )


def save_preferences(user_id: int, prefs: Preferences) -> None:
    """Store the account's settings, creating its row the first time.
    Raises on a database failure."""
    values = asdict(prefs)
    values["suggest_days"] = values.pop("days")
    with Session(engine) as session:
        row = session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        ).scalar_one_or_none()
        if row is None:
            session.add(UserSettings(user_id=user_id, **values))
        else:
            for key, value in values.items():
                setattr(row, key, value)
        session.commit()


def preset_of(prefs: Preferences) -> str:
    """Which preset a saved set of days matches, for the form."""
    for name, days in DAY_PRESETS.items():
        if prefs.days == days:
            return name
    return "custom"
