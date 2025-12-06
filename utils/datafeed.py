from datetime import datetime, timezone
from collections import defaultdict


# ===================== Helper Functions =====================


def _parse_datetime(dt):
    """
    Parse a datetime value that could be either a datetime object or a string.

    Args:
        dt: Either a datetime object or an ISO format string

    Returns:
        datetime object
    """
    if isinstance(dt, datetime):
        return dt
    elif isinstance(dt, str):
        # First try ISO format with timezone (most common from APIs/databases)
        try:
            return datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

        # Try multiple formats commonly returned by Flask/SQLAlchemy
        formats = [
            "%a, %d %b %Y %H:%M:%S %Z",  # 'Mon, 01 Dec 2025 09:00:00 GMT'
            "%Y-%m-%dT%H:%M:%S",  # '2025-12-01T09:00:00'
            "%Y-%m-%dT%H:%M:%S.%f",  # '2025-12-01T09:00:00.123456'
            "%Y-%m-%d %H:%M:%S",  # '2025-12-01 09:00:00'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt, fmt)
            except ValueError:
                continue

        # If none of the formats work, raise an error
        raise ValueError(f"Cannot parse datetime string: {dt}")
    else:
        raise ValueError(f"Cannot parse datetime from {type(dt)}: {dt}")


# ===================== homepage =====================


def build_daily_event_list(event_by_month):
    """
    Convert event_by_month → daily_event_list for the current day.
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
    current_day = now.day

    events = event_by_month.get("events", [])
    daily_events = []

    for event in events:
        # Parse datetime strings to datetime objects if needed
        start_dt = _parse_datetime(event["start_time"])
        end_dt = _parse_datetime(event["end_time"])

        # Filter today event
        if start_dt.day == current_day:
            # Compute integer+fraction hours
            start_int = start_dt.hour + start_dt.minute / 60
            end_int = end_dt.hour + end_dt.minute / 60

            duration = end_int - start_int

            daily_events.append(
                {
                    "id": event["id"],
                    "name": event["name"],
                    "start_time": start_dt.isoformat().replace("+00:00", "Z"),
                    "end_time": end_dt.isoformat().replace("+00:00", "Z"),
                    "location": event["location"],
                    "start_int": start_int,
                    "end_int": end_int,
                    "duration": duration,
                }
            )

    return daily_events


def monthly_events_grouped(event_by_month):
    """
    Convert event_by_month → monthly_event_list grouped by day.

    Output format:
    [
        { "day": 27, "daily_events": [...] },
        { "day": 30, "daily_events": [...] }
    ]
    """

    events = event_by_month.get("events", [])
    days = {}

    for event in events:
        # Parse datetime strings to datetime objects if needed
        start_dt = _parse_datetime(event["start_time"])

        day = start_dt.day

        if day not in days:
            days[day] = []

        days[day].append(event)

    # Convert dict → sorted list by day number
    result = [
        {"day": day, "daily_events": days[day]} for day in sorted(days.keys())
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
        # Parse datetime strings to datetime objects if needed
        start_dt = _parse_datetime(e["start_time"])
        end_dt = _parse_datetime(e["end_time"])

        # Convert string datetime fields to datetime objects for template use
        event_copy = e.copy()
        event_copy["start_time"] = start_dt
        event_copy["end_time"] = end_dt

        day = start_dt.day
        month = start_dt.month
        year = start_dt.year
        full_date_str = datetime(year, month, day).strftime("%A, %d %B %Y")
        daily_groups[full_date_str].append(event_copy)

    # Build the final list sorted by date
    result = [
        {"full_date": date, "daily_events": daily_groups[date]}
        for date in sorted(
            daily_groups.keys(),
            key=lambda d: datetime.strptime(d, "%A, %d %B %Y"),
        )
    ]

    return result


def parse_event_for_datepicker(selected_event: dict) -> dict:
    """
    Takes a selected_event dict and returns a new dict with:
      - original fields preserved
      - start_time_local and end_time_local formatted for
        <input type="datetime-local"> (YYYY-MM-DDTHH:MM)
    """

    def to_datetime_local(value) -> str:
        if not value:
            return ""
        # Parse the datetime (handles both strings and datetime objects)
        dt = _parse_datetime(value)
        return dt.strftime("%Y-%m-%dT%H:%M")

    def to_time_local(value) -> str:
        if not value:
            return ""
        # Parse the datetime (handles both strings and datetime objects)
        dt = _parse_datetime(value)
        return dt.strftime("%H:%M")

    parsed_event = selected_event.copy()

    parsed_event["start_time"] = to_datetime_local(
        selected_event.get("start_time")
    )
    parsed_event["end_time"] = to_time_local(
        selected_event.get("end_time")
    )

    return parsed_event


def parse_incoming_start_and_end_time(
    start_dt_str: str,
    end_time_str: str
) -> dict:
    """
    Takes:
        start_dt_str: "YYYY-MM-DDTHH:MM"  (datetime-local format)
        end_time_str: "HH:MM"             (time input)

    Returns:
        dict with keys:
            'start_time': datetime object
            'end_time': datetime object
    """

    start_dt = datetime.strptime(start_dt_str, "%Y-%m-%dT%H:%M")

    end_h, end_m = end_time_str.split(":")
    end_dt = start_dt.replace(hour=int(end_h), minute=int(end_m))

    return {
        "start_time": start_dt,
        "end_time": end_dt
    }
