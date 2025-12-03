current_day_event = [
    {
        "id": 1, # database
        "name": "Meeting", # database
        "start_time": "2025-12-27T10:00:00Z", # database
        "end_time": "2025-12-27T11:00:00Z", # database
        "location": "Huxley Building", # database
        "start_int": 10, # additional manipulation
        "end_int": 11, # additional manipulation
        "durantion" : 1 # additional manipulation
    },
    {
        "id": 2, 
        "name": "Workout", 
        "start_time": "2025-12-27T18:00:00Z", # database
        "end_time": "2025-12-27T18:30:00Z", # database
        "location": "Huxley Building", # database
        "start_int": 18, # additional manipulation
        "end_int": 18.5, # additional manipulation
        "durantion" : 0.5 # additional manipulation
    },
    {
        "id": 3, 
        "name": "Test", 
        "start": "18.5", 
        "end": "19", 
        "duration": 0.5,
        "start_date": "2025-12-27",
        "start_time": "18:30",
        "end_date": "2025-12-27",
        "end_time": "19:00"
    }
]

current_day_event_2 = [
    {
        "id": 4, 
        "name": "Breakfast Meeting", 
        "start": "8", 
        "end": "9", 
        "duration": 1,
        "start_date": "2025-12-30",
        "start_time": "08:00",
        "end_date": "2025-12-30",
        "end_time": "09:00"
    },
    {
        "id": 5, 
        "name": "Project Review", 
        "start": "14", 
        "end": "15.5", 
        "duration": 1.5,
        "start_date": "2025-12-30",
        "start_time": "14:00",
        "end_date": "2025-12-30",
        "end_time": "15:30"
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