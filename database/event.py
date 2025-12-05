from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Tuple, Any, Optional
from models.db_models.event import Event
from database.db_engine import engine


# Helper functions

def _serialize_event(event: Event, iso_format: bool = False) -> Dict[str, Any]:
    """
    Serialize an Event object to a dictionary.
    
    Args:
        event: Event object to serialize
        iso_format: If True, convert datetimes to ISO format strings
        
    Returns:
        Dictionary representation of the event
    """
    return {
        "id": event.id,
        "name": event.name,
        "start_time": event.start_time.isoformat() if iso_format else event.start_time,
        "end_time": event.end_time.isoformat() if iso_format else event.end_time,
        "location": event.location,
    }


def _validate_event_id(event_id: Any) -> Tuple[Optional[int], Optional[Tuple[Dict, int]]]:
    """
    Validate and convert event_id to integer.
    
    Args:
        event_id: The event ID to validate
        
    Returns:
        Tuple of (validated_id, error_response). 
        If validation succeeds, returns (id, None).
        If validation fails, returns (None, error_tuple).
    """
    try:
        return int(event_id), None
    except (ValueError, TypeError):
        return None, ({"error": "'event_id' must be an integer."}, 400)


def _normalize_data(data: Any) -> Dict[str, Any]:
    """
    Convert data to a standard dictionary format.
    Handles both dict and ImmutableMultiDict (from Flask forms).
    
    Args:
        data: Data to normalize
        
    Returns:
        Dictionary representation of the data
    """
    if hasattr(data, "to_dict"):
        return data.to_dict()
    return data


def _validate_required_fields(data: Dict[str, Any], required_fields: list) -> Optional[Tuple[Dict, int]]:
    """
    Validate that all required fields are present and non-empty.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Error tuple if validation fails, None if validation succeeds
    """
    missing = [
        field
        for field in required_fields
        if field not in data or not data[field]
    ]
    if missing:
        return {"error": f"Missing required fields: {', '.join(missing)}"}, 400
    return None


def _parse_datetime(value: str, field_name: str) -> Tuple[Optional[datetime], Optional[Tuple[Dict, int]]]:
    """
    Parse ISO datetime string.
    
    Args:
        value: ISO datetime string to parse
        field_name: Name of the field (for error messages)
        
    Returns:
        Tuple of (datetime_object, error_response).
        If parsing succeeds, returns (datetime, None).
        If parsing fails, returns (None, error_tuple).
    """
    try:
        return datetime.fromisoformat(value), None
    except (ValueError, TypeError, AttributeError):
        return None, ({"error": f"'{field_name}' must be a valid ISO datetime string."}, 400)


def _validate_datetime_range(start_time: datetime, end_time: datetime) -> Optional[Tuple[Dict, int]]:
    """
    Validate that end_time is after start_time.
    
    Args:
        start_time: Start datetime
        end_time: End datetime
        
    Returns:
        Error tuple if validation fails, None if validation succeeds
    """
    if end_time <= start_time:
        return {"error": "'end_time' must be after 'start_time'."}, 400
    return None


# Main CRUD functions

def get_events() -> Dict[str, Any]:
    """Get all events."""
    try:
        stmt = select(Event)
        with Session(engine) as session:
            events = session.execute(stmt).scalars().unique().all()
            data = [_serialize_event(event) for event in events]
        return {"events": data}
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def get_event_by_id(event_id: Any) -> Tuple[Dict[str, Any], int]:
    """Get a single event by ID."""
    validated_id, error = _validate_event_id(event_id)
    if error:
        return error
    
    try:
        with Session(engine) as session:
            event = session.get(Event, validated_id)
            if not event:
                return {"error": "Event not found."}, 404
            return _serialize_event(event, iso_format=True), 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def create_event(data: Any) -> Tuple[Dict[str, Any], int]:
    """Create a new event."""
    try:
        data = _normalize_data(data)
        
        # Validate required fields
        required_fields = ["name", "start_time", "end_time", "location"]
        error = _validate_required_fields(data, required_fields)
        if error:
            return error
        
        # Parse and validate datetime fields
        start_time, error = _parse_datetime(data["start_time"], "start_time")
        if error:
            return error
        
        end_time, error = _parse_datetime(data["end_time"], "end_time")
        if error:
            return error
        
        # Validate datetime range
        error = _validate_datetime_range(start_time, end_time)
        if error:
            return error
        
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
            return _serialize_event(event, iso_format=True), 201
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def update_event(event_id: Any, data: Any) -> Tuple[Dict[str, Any], int]:
    """Update an existing event."""
    validated_id, error = _validate_event_id(event_id)
    if error:
        return error
    
    try:
        data = _normalize_data(data)
        
        with Session(engine) as session:
            event = session.get(Event, validated_id)
            if not event:
                return {"error": "Event not found."}, 404
            
            # Update datetime fields if provided
            if "start_time" in data and data["start_time"]:
                start_time, error = _parse_datetime(data["start_time"], "start_time")
                if error:
                    return error
                event.start_time = start_time
            
            if "end_time" in data and data["end_time"]:
                end_time, error = _parse_datetime(data["end_time"], "end_time")
                if error:
                    return error
                event.end_time = end_time
            
            # Validate datetime range
            error = _validate_datetime_range(event.start_time, event.end_time)
            if error:
                return error
            
            # Update other fields
            if "name" in data and data["name"]:
                event.name = data["name"]
            if "location" in data and data["location"]:
                event.location = data["location"]
            
            session.commit()
            session.refresh(event)
            return _serialize_event(event, iso_format=True), 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def delete_event(event_id: Any) -> Tuple[Dict[str, str], int]:
    """Delete an event by ID."""
    validated_id, error = _validate_event_id(event_id)
    if error:
        return error
    
    try:
        with Session(engine) as session:
            event = session.get(Event, validated_id)
            if not event:
                return {"error": "Event not found."}, 404
            session.delete(event)
            session.commit()
        return {"message": f"Event {validated_id} deleted."}, 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500
