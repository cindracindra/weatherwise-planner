current_day_event = [
        {"id": 1, "name": "Meeting", "start": "10", "end": "11", "duration": 1},
        {"id": 2, "name": "Workout", "start": "18", "end": "18.5", "duration": 0.5},
        {"id": 3, "name": "Test", "start": "18.5", "end": "19", "duration": 0.5}
        ]

current_month_event = [
        {"day": 27, "full_date": "Thursday, 27 November 2025", "daily_events": current_day_event},
        {"day": 30, "full_date": "Sunday, 30 November 2025", "daily_events": current_day_event}
        ]
    
all_event = [
    {"day": 27, "month": 12, "full_date": "Thursday, 27 November 2025", "daily_events": current_day_event},
    {"day": 30, "month": 12, "full_date": "Sunday, 30 November 2025", "daily_events": current_day_event}
    ]

def dummy_get_daily_event_by_profile(profile_id):
    profile_id

    return current_day_event

def dummy_get_monthly_event_by_profile(profile_id):
    profile_id
    
    return current_month_event

def dummy_get_all_event_by_profile(profile_id):
    profile_id
    
    return all_event

def dummy_get_event_by_id(event_id):
    found_event = None
    
    for day in all_event:
        for event in day["daily_events"]:
            if event["id"] == event_id:
                found_event = event
                break  
        if found_event:
            break
    
    return(found_event)