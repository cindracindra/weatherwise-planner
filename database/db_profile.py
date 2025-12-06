from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Dict, Tuple, Any
from flask import Response
from models.db_models.profile import Profile
from database.engine import engine
from utils.response import StatusCode, build_response
from utils.request import normalize_data, validate_id, validate_required_fields


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


# Main CRUD functions


def get_profiles() -> Tuple[Response, int]:
    """Get all profiles."""
    try:
        stmt = select(Profile)
        with Session(engine) as session:
            profiles = session.execute(stmt).scalars().unique().all()
            data = [_serialize_profile(profile) for profile in profiles]
        return build_response(StatusCode.OK, {"profiles": data})
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def get_profile_by_id(profileid: Any) -> Tuple[Response, int]:
    """Get a single profile by ID."""
    validated_id = validate_id(profileid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return build_response(
            StatusCode.BAD_REQUEST,
            {"error": "'profileid' must be an integer."},
        )

    try:
        with Session(engine) as session:
            profile = session.get(Profile, validated_id)
            if not profile:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {"error": f"Profile with id {validated_id} not found."},
                )
            return build_response(StatusCode.OK, _serialize_profile(profile))
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def create_profile(data: Any) -> Tuple[Response, int]:
    """Create a new profile."""
    try:
        data = normalize_data(data)

        # Validate required fields
        required_fields = ["name"]
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

        # Create profile
        with Session(engine) as session:
            profile = Profile(name=data["name"])
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return build_response(
                StatusCode.CREATED, _serialize_profile(profile)
            )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def delete_profile(profileid: Any) -> Tuple[Response, int]:
    """Delete a profile by ID."""
    validated_id = validate_id(profileid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return build_response(
            StatusCode.BAD_REQUEST,
            {"error": "'profileid' must be an integer."},
        )

    try:
        with Session(engine) as session:
            profile = session.get(Profile, validated_id)
            if not profile:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {"error": f"Profile with id {validated_id} not found."},
                )
            session.delete(profile)
            session.commit()
        return build_response(
            StatusCode.OK, {"message": f"Profile {validated_id} deleted."}
        )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )
