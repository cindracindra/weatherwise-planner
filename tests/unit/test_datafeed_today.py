"""Today's timeline picks events by London's date, not UTC's."""

from utils.datafeed import build_daily_event_list

EVENTS = {"events": [
    {"id": 1, "name": "Late film", "start_time": "2026-10-07T23:00:00",
     "end_time": "2026-10-07T23:45:00", "location": "Soho"},
    {"id": 2, "name": "Breakfast", "start_time": "2026-10-08T08:00:00",
     "end_time": "2026-10-08T09:00:00", "location": "Home"},
]}


def test_today_is_the_day_passed_in():
    # 00:30 in London on the 8th is still the 7th in UTC
    names = [e["name"] for e in build_daily_event_list(EVENTS, today_day=8)]
    assert names == ["Breakfast"]
