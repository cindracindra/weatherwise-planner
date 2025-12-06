from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Tuple, Any
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


# Main CRUD functions


def get_events() -> Tuple[Response, int]:
    """Get all events."""
    try:
        stmt = select(Event)
        with Session(engine) as session:
            events = session.execute(stmt).scalars().unique().all()
            data = [
                _serialize_event(event, iso_format=True) for event in events
            ]
        return build_response(StatusCode.OK, {"events": data})
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def get_event_by_id(eventid: Any) -> Tuple[Response, int]:
    """Get a single event by ID."""
    validated_id = validate_id(eventid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return build_response(
            StatusCode.BAD_REQUEST, {"error": "'eventid' must be an integer."}
        )

    try:
        with Session(engine) as session:
            event = session.get(Event, validated_id)
            if not event:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {"error": f"Event with id {validated_id} not found."},
                )
            return build_response(
                StatusCode.OK, _serialize_event(event, iso_format=True)
            )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def create_event(data: Any) -> Tuple[Response, int]:
    """Create a new event."""
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
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return build_response(
                StatusCode.CREATED, _serialize_event(event, iso_format=True)
            )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def update_event(eventid: Any, data: Any) -> Tuple[Response, int]:
    """Update an existing event."""
    validated_id = validate_id(eventid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return build_response(
            StatusCode.BAD_REQUEST, {"error": "'eventid' must be an integer."}
        )

    try:
        data = normalize_data(data)

        with Session(engine) as session:
            event = session.get(Event, validated_id)
            if not event:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {"error": f"Event with id {validated_id} not found."},
                )

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
            return build_response(
                StatusCode.OK, _serialize_event(event, iso_format=True)
            )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def delete_event(eventid: Any) -> Tuple[Response, int]:
    """Delete an event by ID."""
    validated_id = validate_id(eventid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return build_response(
            StatusCode.BAD_REQUEST, {"error": "'eventid' must be an integer."}
        )

    try:
        with Session(engine) as session:
            event = session.get(Event, validated_id)
            if not event:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {"error": f"Event with id {validated_id} not found."},
                )
            session.delete(event)
            session.commit()
        return build_response(
            StatusCode.OK, {"message": f"Event {validated_id} deleted."}
        )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )
