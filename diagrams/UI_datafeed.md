# OUTGOING TO HTML - function to be called in the app.py in the routes

## Main homepage  

- calendar_matrix=calendar_matrix >> DONE via get_full_calendar(today["year"], today["month"])

- hourly_forecast=hourly_forecast >> DONE via get_hourly_forecast_today()

- today_detail=today >> DONE via get_today_detail()

- profile_id=profile_id >> DONE via html args

- profile_list=profile_list["profiles"] >> DONE via get_profiles()

- monthly_event_list=monthly_event_list >> PENDING, need interim function
expected return [
    {
        "day": 27, 
        "daily_events": current_day_event
    },
    {
        "day": 30,  
        "daily_events": current_day_event_2
    }
]

- daily_event_list=daily_event_list >> PENDING, need interim function
expected return [
    {
        "id": 1, # database
        "name": "Meeting", # database
        "start_time": "2025-12-27T10:00:00Z", # database
        "end_time": "2025-12-27T11:00:00Z", # database
        "location": "Huxley Building", # database
        "start_int": 10, # additional manipulation
        "end_int": 11, # additional manipulation
        "durantion" : 1 # additional manipulation
    }
]


## Event Management page 

- profile_id=profile_id >> DONE via html args

- all_event=all_event >> PENDING, need interim function
expected return [
    { 
        "full_date": "Thursday, 27 December 2025", 
        "daily_events": current_day_event
    },
    {
        "full_date": "Sunday, 30 December 2025", 
        "daily_events": current_day_event_2
    }
]

- selected_event=selected_event >> PENDING, need interim function
expected return [
    {
        "id": 1, # database
        "name": "Meeting", # database
        "start_time": "2025-12-27T10:00:00Z", # database
        "end_time": "2025-12-27T11:00:00Z", # database
        "location": "Huxley Building", # database
    }
]

## Profile Management page 

- profile_list=profile_list["profiles"] >> DONE via get_profiles()