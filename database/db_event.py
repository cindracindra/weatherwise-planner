from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Tuple, Any, Optional
from flask import Response
from models.db_models.event import Event
from database.engine import engine
from utils.response import StatusCode, build_response
from utils.request import (
    normalize_data,
    validate_id,
    validate_required_fields,
    parse_datetime,
    validate_datetime_range,
)

# Every function takes the id of the account the request is for. An event
# that belongs to someone else is treated exactly like one that does not
# exist, so the API never reveals other people's events.


# Helper functions


def _serialize_event(event: Event, iso_format: bool = True) -> Dict[str, Any]:
    return {
        "id": event.id,
        "name": event.name,
        "start_time": (
            event.start_time.isoformat() if iso_format else event.start_time
        ),
        "end_time": (
            event.end_time.isoformat() if iso_format else event.end_time
        ),
        "location": event.location,
    }


def _not_found(eventid: int) -> Tuple[Response, int]:
    return build_response(
        StatusCode.NOT_FOUND, {"error": f"Event with id {eventid} not found."}
    )


def _bad_id() -> Tuple[Response, int]:
    return build_response(
        StatusCode.BAD_REQUEST, {"error": "'eventid' must be an integer."}
    )


def _owned(session: Session, eventid: int, user_id: int) -> Optional[Event]:
    """The event if it exists and belongs to user_id, else None."""
    event = session.get(Event, eventid)
    if event is None or event.user_id != user_id:
        return None
    return event


def _month_bounds(year: int, month: int) -> Tuple[datetime, datetime]:
    start = datetime(year, month, 1)
    if month == 12:
        return start, datetime(year + 1, 1, 1)
    return start, datetime(year, month + 1, 1)


# Main CRUD functions


def get_events(
    user_id: int, year: Optional[int] = None, month: Optional[int] = None
) -> Tuple[Response, int]:
    """Get the account's events, optionally only those starting in a month."""
    try:
        stmt = select(Event).where(Event.user_id == user_id)
        if year and month:
            start, end = _month_bounds(year, month)
            stmt = stmt.where(
                Event.start_time >= start, Event.start_time < end
            )
        stmt = stmt.order_by(Event.start_time)
        with Session(engine) as session:
            events = session.execute(stmt).scalars().all()
            data = [_serialize_event(event) for event in events]
        return build_response(StatusCode.OK, {"events": data})
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def get_event_by_id(eventid: Any, user_id: int) -> Tuple[Response, int]:
    """Get one of the account's events by ID."""
    validated_id = validate_id(eventid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return _bad_id()

    try:
        with Session(engine) as session:
            event = _owned(session, validated_id, user_id)
            if not event:
                return _not_found(validated_id)
            return build_response(StatusCode.OK, _serialize_event(event))
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def create_event(data: Any, user_id: int) -> Tuple[Response, int]:
    """Create a new event owned by the account."""
    try:
        data = normalize_data(data)

        # Validate required fields
        required_fields = ["name", "start_time", "end_time", "location"]
        field_error = validate_required_fields(data, required_fields)
        if field_error is not None:
            missing = [
                field
                for field in required_fields
                if field not in data or not data[field]
            ]
            return build_response(
                StatusCode.BAD_REQUEST,
                {"error": f"Missing required fields: {', '.join(missing)}"},
            )

        # Parse and validate datetime fields
        start_time = parse_datetime(data["start_time"])
        if not isinstance(start_time, datetime):
            return build_response(
                StatusCode.BAD_REQUEST,
                {"error": "Invalid datetime format for 'start_time'."},
            )

        end_time = parse_datetime(data["end_time"])
        if not isinstance(end_time, datetime):
            return build_response(
                StatusCode.BAD_REQUEST,
                {"error": "Invalid datetime format for 'end_time'."},
            )

        # Validate datetime range
        range_error = validate_datetime_range(start_time, end_time)
        if range_error is not None:
            return build_response(
                StatusCode.BAD_REQUEST,
                {"error": "End time must be after start time."},
            )

        # Create event
        with Session(engine) as session:
            event = Event(
                name=data["name"],
                start_time=start_time,
                end_time=end_time,
                location=data["location"],
                user_id=user_id,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return build_response(StatusCode.CREATED, _serialize_event(event))
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def update_event(
    eventid: Any, data: Any, user_id: int
) -> Tuple[Response, int]:
    """Update one of the account's events."""
    validated_id = validate_id(eventid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return _bad_id()

    try:
        data = normalize_data(data)

        with Session(engine) as session:
            event = _owned(session, validated_id, user_id)
            if not event:
                return _not_found(validated_id)

            # Update datetime fields if provided
            if "start_time" in data and data["start_time"]:
                start_time = parse_datetime(data["start_time"])
                if not isinstance(start_time, datetime):
                    return build_response(
                        StatusCode.BAD_REQUEST,
                        {"error": "Invalid datetime format for 'start_time'."},
                    )
                event.start_time = start_time

            if "end_time" in data and data["end_time"]:
                end_time = parse_datetime(data["end_time"])
                if not isinstance(end_time, datetime):
                    return build_response(
                        StatusCode.BAD_REQUEST,
                        {"error": "Invalid datetime format for 'end_time'."},
                    )
                event.end_time = end_time

            # Validate datetime range
            range_error = validate_datetime_range(
                event.start_time, event.end_time
            )
            if range_error is not None:
                return build_response(
                    StatusCode.BAD_REQUEST,
                    {"error": "End time must be after start time."},
                )

            # Update other fields
            if "name" in data and data["name"]:
                event.name = data["name"]
            if "location" in data and data["location"]:
                event.location = data["location"]

            session.commit()
            session.refresh(event)
            return build_response(StatusCode.OK, _serialize_event(event))
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def delete_event(eventid: Any, user_id: int) -> Tuple[Response, int]:
    """Delete one of the account's events."""
    validated_id = validate_id(eventid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return _bad_id()

    try:
        with Session(engine) as session:
            event = _owned(session, validated_id, user_id)
            if not event:
                return _not_found(validated_id)
            session.delete(event)
            session.commit()
        return build_response(
            StatusCode.OK, {"message": f"Event {validated_id} deleted."}
        )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )
