from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Dict, Tuple, Any, Optional
from models.db_models.event import Event
from models.db_models.profile import Profile
from models.db_models.eventxprofile import EventXProfile
from database.db_engine import engine


# Helper functions

def _serialize_eventxprofile(event_profile: EventXProfile, include_id: bool = False) -> Dict[str, Any]:
    """
    Serialize an EventXProfile object to a dictionary.
    
    Args:
        event_profile: EventXProfile object to serialize
        include_id: Whether to include the internal ID
        
    Returns:
        Dictionary representation of the eventxprofile
    """
    result = {
        "event_id": event_profile.eventid,
        "profile_id": event_profile.profileid,
    }
    if include_id:
        result["id"] = event_profile.id
    return result


def _validate_eventxprofile_id(event_profile_id: Any) -> Tuple[Optional[int], Optional[Tuple[Dict, int]]]:
    """
    Validate and convert event_profile_id to integer.
    
    Args:
        event_profile_id: The event profile ID to validate
        
    Returns:
        Tuple of (validated_id, error_response).
        If validation succeeds, returns (id, None).
        If validation fails, returns (None, error_tuple).
    """
    try:
        return int(event_profile_id), None
    except (ValueError, TypeError):
        return None, ({"error": "'event_profile_id' must be an integer."}, 400)


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


def _validate_integer_ids(data: Dict[str, Any], field_names: list) -> Tuple[Optional[Dict[str, int]], Optional[Tuple[Dict, int]]]:
    """
    Validate and convert multiple ID fields to integers.
    
    Args:
        data: Data dictionary containing ID fields
        field_names: List of field names to validate
        
    Returns:
        Tuple of (validated_ids_dict, error_response).
        If validation succeeds, returns (dict_of_ids, None).
        If validation fails, returns (None, error_tuple).
    """
    try:
        validated_ids = {field: int(data[field]) for field in field_names}
        return validated_ids, None
    except (ValueError, TypeError, KeyError):
        field_str = "' and '".join(field_names)
        return None, ({"error": f"'{field_str}' must be integers."}, 400)


# Main CRUD functions

def get_eventxprofiles() -> Dict[str, Any]:
    """Get all event-profile associations."""
    try:
        stmt = select(EventXProfile)
        with Session(engine) as session:
            event_profiles = session.execute(stmt).scalars().all()
            data = [_serialize_eventxprofile(ep) for ep in event_profiles]
        return {"event_profiles": data}
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def get_eventxprofile_by_id(event_profile_id: Any) -> Tuple[Dict[str, Any], int]:
    """Get a single event-profile association by ID."""
    validated_id, error = _validate_eventxprofile_id(event_profile_id)
    if error:
        return error
    
    try:
        with Session(engine) as session:
            event_profile = session.get(EventXProfile, validated_id)
            if not event_profile:
                return {"error": "EventXProfile not found."}, 404
            return _serialize_eventxprofile(event_profile, include_id=True), 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def create_eventxprofile(data: Any) -> Tuple[Dict[str, Any], int]:
    """Create a new event-profile association."""
    try:
        data = _normalize_data(data)
        
        # Validate required fields
        required_fields = ["eventid", "profileid"]
        error = _validate_required_fields(data, required_fields)
        if error:
            return error
        
        # Validate integer IDs
        validated_ids, error = _validate_integer_ids(data, ["eventid", "profileid"])
        if error:
            return error
        
        eventid = validated_ids["eventid"]
        profileid = validated_ids["profileid"]
        
        # Check if event and profile exist
        with Session(engine) as session:
            event = session.get(Event, eventid)
            profile = session.get(Profile, profileid)
            
            if not event or not profile:
                return {"error": "Event or Profile not found."}, 404
            
            # Create the association
            event_profile = EventXProfile(eventid=eventid, profileid=profileid)
            session.add(event_profile)
            session.commit()
            session.refresh(event_profile)
            return _serialize_eventxprofile(event_profile, include_id=True), 201
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def delete_eventxprofile(event_profile_id: Any) -> Tuple[Dict[str, str], int]:
    """Delete an event-profile association by ID."""
    validated_id, error = _validate_eventxprofile_id(event_profile_id)
    if error:
        return error
    
    try:
        with Session(engine) as session:
            event_profile = session.get(EventXProfile, validated_id)
            if not event_profile:
                return {"error": "EventXProfile not found."}, 404
            session.delete(event_profile)
            session.commit()
        return {"message": f"EventXProfile {validated_id} deleted."}, 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500
