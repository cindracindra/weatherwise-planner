"""Tests for database/db_settings.py: the settings form and the defaults."""

from unittest.mock import patch

import pytest

from database.db_settings import (
    clean_preferences, get_preferences, preset_of, save_preferences,
)
from models.api_models.suggestion import Preferences
from models.db_models.settings import UserSettings

FORM = {"days": "every", "weekday_start": "18", "weekday_end": "21",
        "weekend_start": "9", "weekend_end": "18", "show_today": "on"}


@pytest.fixture
def session():
    with patch("database.db_settings.Session") as session_class:
        yield session_class.return_value.__enter__.return_value


def test_defaults_are_every_day_evenings_and_weekend_days():
    prefs = Preferences()
    assert prefs.days == "0123456"
    assert (prefs.weekday_start, prefs.weekday_end) == (18, 21)
    assert (prefs.weekend_start, prefs.weekend_end) == (9, 18)
    assert prefs.show_today and not prefs.skip_busy_days


def test_an_account_without_settings_gets_the_defaults(session):
    session.execute.return_value.scalar_one_or_none.return_value = None
    assert get_preferences(7) == Preferences()


def test_presets_and_custom_days():
    assert clean_preferences(FORM).days == "0123456"
    assert clean_preferences(dict(FORM, days="weekends")).days == "56"
    custom = dict(FORM, days="custom", day_4="on", day_5="on", day_6="on")
    assert clean_preferences(custom).days == "456"


def test_tick_boxes():
    prefs = clean_preferences(dict(FORM, skip_busy_days="on"))
    assert prefs.skip_busy_days and prefs.show_today
    prefs = clean_preferences({k: v for k, v in FORM.items() if k != "show_today"})
    assert not prefs.show_today


@pytest.mark.parametrize("change, message", [
    ({"days": "custom"}, "at least one day"),
    ({"days": "fortnightly"}, "which days"),
    ({"weekday_start": "21"}, "On weekdays, the end must be after"),
    ({"weekend_end": "8"}, "At weekends, the end must be after"),
    ({"weekend_end": "25"}, "between 00:00 and 24:00"),
    ({"weekday_start": ""}, "start and end time"),
])
def test_bad_settings_are_refused(change, message):
    with pytest.raises(ValueError, match=message):
        clean_preferences(dict(FORM, **change))


def test_preset_of():
    assert preset_of(Preferences()) == "every"
    assert preset_of(Preferences(days="56")) == "weekends"
    assert preset_of(Preferences(days="45")) == "custom"


def test_saving_creates_the_row_once_then_updates_it(session):
    session.execute.return_value.scalar_one_or_none.return_value = None
    save_preferences(7, Preferences(days="56"))
    row = session.add.call_args[0][0]
    assert row.user_id == 7 and row.suggest_days == "56"

    existing = UserSettings(user_id=7, suggest_days="0123456")
    session.execute.return_value.scalar_one_or_none.return_value = existing
    session.add.reset_mock()
    save_preferences(7, Preferences(days="5", show_today=False))
    session.add.assert_not_called()
    assert existing.suggest_days == "5" and existing.show_today is False
