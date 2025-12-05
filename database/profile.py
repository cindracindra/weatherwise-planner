from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Dict, Tuple, Any, Optional
from models.db_models.profile import Profile
from database.db_engine import engine


# Helper functions

def _serialize_profile(profile: Profile) -> Dict[str, Any]:
    """
    Serialize a Profile object to a dictionary.
    
    Args:
        profile: Profile object to serialize
        
    Returns:
        Dictionary representation of the profile
    """
    return {
        "id": profile.id,
        "name": profile.name,
    }


def _validate_profile_id(profile_id: Any) -> Tuple[Optional[int], Optional[Tuple[Dict, int]]]:
    """
    Validate and convert profile_id to integer.
    
    Args:
        profile_id: The profile ID to validate
        
    Returns:
        Tuple of (validated_id, error_response).
        If validation succeeds, returns (id, None).
        If validation fails, returns (None, error_tuple).
    """
    try:
        return int(profile_id), None
    except (ValueError, TypeError):
        return None, ({"error": "'profile_id' must be an integer."}, 400)


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


# Main CRUD functions

def get_profiles() -> Dict[str, Any]:
    """Get all profiles."""
    try:
        stmt = select(Profile)
        with Session(engine) as session:
            profiles = session.execute(stmt).scalars().unique().all()
            data = [_serialize_profile(profile) for profile in profiles]
        return {"profiles": data}
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def get_profile_by_id(profile_id: Any) -> Tuple[Dict[str, Any], int]:
    """Get a single profile by ID."""
    validated_id, error = _validate_profile_id(profile_id)
    if error:
        return error
    
    try:
        with Session(engine) as session:
            profile = session.get(Profile, validated_id)
            if not profile:
                return {"error": "Profile not found."}, 404
            return _serialize_profile(profile), 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def create_profile(data: Any) -> Tuple[Dict[str, Any], int]:
    """Create a new profile."""
    try:
        data = _normalize_data(data)
        
        # Validate required fields
        required_fields = ["profile_name"]
        error = _validate_required_fields(data, required_fields)
        if error:
            return error
        
        # Create profile
        with Session(engine) as session:
            profile = Profile(name=data["profile_name"])
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return _serialize_profile(profile), 201
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def delete_profile(profile_id: Any) -> Tuple[Dict[str, str], int]:
    """Delete a profile by ID."""
    validated_id, error = _validate_profile_id(profile_id)
    if error:
        return error
    
    try:
        with Session(engine) as session:
            profile = session.get(Profile, validated_id)
            if not profile:
                return {"error": "Profile not found."}, 404
            session.delete(profile)
            session.commit()
        return {"message": f"Profile {validated_id} deleted."}, 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500
