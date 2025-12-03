from datetime import datetime

current_day_event = [
{
        "id": 1,
        "name": "Meeting",
        "start_time": datetime(2025, 12, 27, 10, 0, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo), # Assuming original was UTC
        "end_time": datetime(2025, 12, 27, 11, 0, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo),
        "location": "Huxley Building",
        "start_int": 10.0,
        "end_int": 11.0,
        "duration": 1.0
    },
    {
        "id": 2,
        "name": "Workout",
        "start_time": datetime(2025, 12, 27, 18, 0, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo), # Assuming original was UTC
        "end_time": datetime(2025, 12, 27, 18, 30, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo),
        "location": "Huxley Building",
        "start_int": 18.0,
        "end_int": 18.5,
        "duration": 0.5
    },
    {
        "id": 3,
        "name": "Test",
        "start_time": datetime(2025, 12, 27, 18, 30, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo),
        "end_time": datetime(2025, 12, 27, 19, 0, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo),
        "location": "N/A",
        "start_int": 18.5,
        "end_int": 19.0,
        "duration": 0.5
    }
]

current_day_event_2 = [
    {
        "id": 4,
        "name": "Breakfast Meeting",
        "start_time": datetime(2025, 12, 30, 8, 0, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo),
        "end_time": datetime(2025, 12, 30, 9, 0, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo),
        "location": "N/A",
        "start_int": 8.0,
        "end_int": 9.0,
        "duration": 1.0
    },
    {
        "id": 5,
        "name": "Project Review",
        "start_time": datetime(2025, 12, 30, 14, 0, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo),
        "end_time": datetime(2025, 12, 30, 15, 30, tzinfo=None).replace(tzinfo=datetime.now().astimezone().tzinfo),
        "location": "N/A",
        "start_int": 14.0,
        "end_int": 15.5,
        "duration": 1.5
    }
]

current_month_event = [
    {
        "day": 27, 
        "daily_events": current_day_event
    },
    {
        "day": 30,  
        "daily_events": current_day_event_2
    }
]

all_event = [
    {
        "full_date": "Thursday, 27 December 2025", 
        "daily_events": current_day_event
    },
    { 
        "full_date": "Sunday, 30 December 2025", 
        "daily_events": current_day_event_2
    }
]

def dummy_get_daily_event_by_profile(profile_id):
    profile_id
    
#     current_day_event = [
#     {
#         "id": 1, # database
#         "name": "Meeting", # database
#         "start_time": "2025-12-27T10:00:00Z", # database
#         "end_time": "2025-12-27T11:00:00Z", # database
#         "location": "Huxley Building", # database
#         "start_int": 10, # additional manipulation
#         "end_int": 11, # additional manipulation
#         "durantion" : 1 # additional manipulation
#     }
# ]


    return current_day_event

def dummy_get_monthly_event_by_profile(profile_id):
    profile_id
    
#     current_month_event = [
#     {
#         "day": 27, 
#         "daily_events": current_day_event
#     },
#     {
#         "day": 30,  
#         "daily_events": current_day_event_2
#     }
# ]
    
    return current_month_event

def dummy_get_all_event_by_profile(profile_id):
    profile_id
    
#     all_event = [
#     { 
#         "full_date": "Thursday, 27 December 2025", 
#         "daily_events": current_day_event
#     },
#     {
#         "full_date": "Sunday, 30 December 2025", 
#         "daily_events": current_day_event_2
#     }
# ]
    
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