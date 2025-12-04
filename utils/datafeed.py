from datetime import datetime, timezone
from collections import defaultdict


# ===================== homepage ===================== 




def build_daily_event_list(event_by_profile):
    """
    Convert event_by_profile → daily_event_list for the current day.
    Adds start_int, end_int, and duration to each event.
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
    """

    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month
    current_day = now.day

    events = event_by_profile.get("events", [])
    daily_events = []

    for event in events:
        start_dt = event["start_time"]
        end_dt = event["end_time"]

        # Filter today event
        if (
            start_dt.year == current_year and
            start_dt.month == current_month and
            start_dt.day == current_day
        ):
            # Compute integer+fraction hours
            start_int = start_dt.hour + start_dt.minute / 60
            end_int = end_dt.hour + end_dt.minute / 60

            duration = end_int - start_int

            daily_events.append({
                "id": event["id"],
                "name": event["name"],
                "start_time": start_dt.isoformat().replace("+00:00", "Z"),
                "end_time": end_dt.isoformat().replace("+00:00", "Z"),
                "location": event["location"],
                "start_int": start_int,
                "end_int": end_int,
                "duration": duration
            })

    return daily_events

def monthly_events_grouped(event_by_profile):
    """
    Convert event_by_profile → monthly_event_list
    using *current year* and *current month* automatically.

    Output format:
    [
        { "day": 27, "daily_events": [...] },
        { "day": 30, "daily_events": [...] }
    ]
    """

    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month

    events = event_by_profile.get("events", [])
    days = {}

    for event in events:
        start_dt = event["start_time"]

        # Only include events happening this month
        if start_dt.year != current_year or start_dt.month != current_month:
            continue

        day = start_dt.day

        if day not in days:
            days[day] = []

        days[day].append(event)

    # Convert dict → sorted list by day number
    result = [
        {"day": day, "daily_events": days[day]}
        for day in sorted(days.keys())
    ]

    return result


# ===================== event management page ===================== 


def group_all_events_by_full_date(event_by_profile):
    """
    Groups all events by their full date (e.g., "Thursday, 27 December 2025").
    Returns:
    [
        {
            "full_date": "Thursday, 27 December 2025",
            "daily_events": [ ...events on that day... ]
        },
        ...
    ]
    """
    events = event_by_profile.get("events", [])
    daily_groups = defaultdict(list)

    for e in events:
        day = e["start_time"].day
        month = e["start_time"].month
        year = e["start_time"].year
        full_date_str = datetime(year, month, day).strftime("%A, %d %B %Y")
        daily_groups[full_date_str].append(e)

    # Build the final list sorted by date
    result = [
        {"full_date": date, "daily_events": daily_groups[date]}
        for date in sorted(
            daily_groups.keys(),
            key=lambda d: datetime.strptime(d, "%A, %d %B %Y")
        )
    ]

    return result


def parse_event_for_datepicker(selected_event: dict) -> dict:
    """
    Takes a selected_event dict and returns a new dict with:
      - original fields preserved
      - start_time_local and end_time_local formatted for <input type="datetime-local">
        (YYYY-MM-DDTHH:MM)
    """
    def to_datetime_local(value: str) -> str:
        if not value:
            return ""
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%dT%H:%M")

    parsed_event = selected_event.copy()

    parsed_event['start_time'] = to_datetime_local(selected_event.get('start_time'))
    parsed_event['end_time'] = to_datetime_local(selected_event.get('end_time'))

    return parsed_event