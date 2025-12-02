from api.event_profile_api import get_event_by_profile

def get_daily_event_by_profile(profile_name):
    profile_name

    current_day_event = [
        {"id": 1, "name": "Meeting", "start": "10", "end": "11", "duration": 1},
        {"id": 2, "name": "Workout", "start": "18", "end": "18.5", "duration": 0.5},
        {"id": 3, "name": "Test", "start": "18.5", "end": "19", "duration": 0.5}
        ]

    return current_day_event

def get_monthly_event_by_profile(profile_name):
    profile_name

    current_day_event = [
        {"id": 1, "name": "Meeting", "start": "10", "end": "11", "duration": 1},
        {"id": 2, "name": "Workout", "start": "18", "end": "18.5", "duration": 0.5},
        {"id": 3, "name": "Test", "start": "18.5", "end": "19", "duration": 0.5}
        ]

    current_month_event = [
        {"day": 27, "full_date": "Thursday, 27 November 2025", "daily_events": current_day_event},
        {"day": 30, "full_date": "Sunday, 30 November 2025", "daily_events": current_day_event}
        ]

    return current_month_event



