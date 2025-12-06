from sqlalchemy import select, extract
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Dict, List, Any, Tuple
from flask import Response
from models.db_models.event import Event
from models.db_models.eventxprofile import EventXProfile
from database.engine import engine
from utils.response import StatusCode, build_response


# Helper functions


def _serialize_event(event: Event) -> Dict[str, Any]:
    """
    Serialize an Event object to a dictionary.

    Args:
        event: Event object to serialize

    Returns:
        Dictionary representation of the event
    """
    return {
        "id": event.id,
        "name": event.name,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "location": event.location,
    }


def _serialize_eventxprofile(eventxprofile: EventXProfile) -> Dict[str, Any]:
    """
    Serialize an EventXProfile object to a dictionary.

    Args:
        eventxprofile: EventXProfile object to serialize

    Returns:
        Dictionary representation of the eventxprofile
    """
    return {
        "id": eventxprofile.id,
        "event_id": eventxprofile.eventid,
        "profile_id": eventxprofile.profileid,
    }


def _get_events_by_profile_query(
    profile_id: int, year: int = None, month: int = None, day: int = None
):
    """
    Build a SQLAlchemy query to get events by profile ID with
    optional date filters.

    Args:
        profile_id: The profile ID to filter events
        year: Optional year filter
        month: Optional month filter (1-12)
        day: Optional day filter (1-31)

    Returns:
        SQLAlchemy select statement
    """
    conditions = [EventXProfile.profileid == profile_id]

    if year is not None:
        conditions.append(extract("year", Event.start_time) == year)
    if month is not None:
        conditions.append(extract("month", Event.start_time) == month)
    if day is not None:
        conditions.append(extract("day", Event.start_time) == day)

    return (
        select(Event)
        .join(Event.eventxprofile)
        .where(*conditions)
        .options(
            joinedload(Event.eventxprofile).joinedload(EventXProfile.profile)
        )
    )


def _execute_events_query(stmt) -> List[Dict[str, Any]]:
    """
    Execute a query and serialize the results.

    Args:
        stmt: SQLAlchemy select statement

    Returns:
        List of serialized event dictionaries
    """
    with Session(engine) as session:
        events = session.execute(stmt).scalars().unique().all()
        return [_serialize_event(event) for event in events]


# Main functions


def get_events_by_profile_id(profile_id: int) -> Tuple[Response, int]:
    """
    Get all events for a specific profile.

    Args:
        profile_id: The profile ID to filter events

    Returns:
        Dictionary containing list of events
    """
    stmt = _get_events_by_profile_query(profile_id)
    data = _execute_events_query(stmt)
    return build_response(StatusCode.OK, {"events": data})


def get_events_by_profile_id_by_month(
    profile_id: int, year: int, month: int
) -> Tuple[Response, int]:
    """
    Get events for a specific profile filtered by year and month.

    Args:
        profile_id: The profile ID to filter events
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        Dictionary containing list of events for the specified month
    """
    stmt = _get_events_by_profile_query(profile_id, year=year, month=month)
    data = _execute_events_query(stmt)
    return build_response(StatusCode.OK, {"events": data})


def create_event_and_profile_association(
    name: str,
    start_time: datetime,
    end_time: datetime,
    location: str,
    profile_id: int,
) -> tuple[Response, int]:
    """
    Create an event and its corresponding EventXProfile entry in
    a single transaction.

    Args:
        name: Event name
        start_time: Event start time (datetime object)
        end_time: Event end time (datetime object)
        location: Event location
        profile_id: The profile ID to associate with the event

    Returns:
        Tuple of (data dictionary, HTTP status code)
    """
    try:
        with Session(engine) as session:
            # Create the event
            new_event = Event(
                name=name,
                start_time=start_time,
                end_time=end_time,
                location=location,
            )

            # Add and flush to get the event ID
            session.add(new_event)
            session.flush()  # This assigns the ID to new_event

            # Create the EventXProfile entry
            eventxprofile = EventXProfile(
                eventid=new_event.id, profileid=profile_id
            )

            # Add and commit both
            session.add(eventxprofile)
            session.commit()

            # Return the created data
            return build_response(
                StatusCode.CREATED,
                {
                    "event": _serialize_event(new_event),
                    "eventxprofile": _serialize_eventxprofile(eventxprofile),
                },
            )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def delete_event_and_profile_association(
    event_id: int,
) -> tuple[Response, int]:
    """
    Delete an event and all its corresponding EventXProfile entries
    in a single transaction.

    Args:
        event_id: The ID of the event to delete

    Returns:
        Tuple of (data dictionary, HTTP status code)
    """
    try:
        with Session(engine) as session:
            # Find the event
            event = session.get(Event, event_id)

            if not event:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {"error": f"Event with id {event_id} not found."},
                )

            # Store event data before deletion
            event_data = _serialize_event(event)

            # Find and delete all EventXProfile entries for this event
            stmt = select(EventXProfile).where(
                EventXProfile.eventid == event_id
            )
            eventxprofiles = session.execute(stmt).scalars().all()

            deleted_profiles = [
                _serialize_eventxprofile(ep) for ep in eventxprofiles
            ]

            for ep in eventxprofiles:
                session.delete(ep)

            # Delete the event
            session.delete(event)
            session.commit()

            return build_response(
                StatusCode.OK,
                {
                    "deleted_event": event_data,
                    "deleted_eventxprofiles": deleted_profiles,
                    "count": len(deleted_profiles),
                },
            )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )
