from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Dict, Tuple, Any, Optional
from flask import Response
from models.db_models.event import Event
from models.db_models.profile import Profile
from models.db_models.eventxprofile import EventXProfile
from database.engine import engine
from utils.response import StatusCode, build_response
from utils.request import normalize_data, validate_id, validate_required_fields


# Helper functions


def _serialize_eventxprofile(
    eventxprofile: EventXProfile, include_id: bool = True
) -> Dict[str, Any]:
    result = {
        "eventid": eventxprofile.eventid,
        "profileid": eventxprofile.profileid,
    }
    if include_id:
        result["id"] = eventxprofile.id
    return result


def _validate_integer_ids(
    data: Dict[str, Any], field_names: list
) -> Tuple[Optional[Dict[str, int]], Optional[Tuple[Dict, int]]]:
    try:
        validated_ids = {field: int(data[field]) for field in field_names}
        return validated_ids, None
    except (ValueError, TypeError, KeyError):
        field_str = "' and '".join(field_names)
        return None, (
            {"error": f"Fields '{field_str}' must be integers."},
            StatusCode.BAD_REQUEST.value,
        )


# Main CRUD functions


def get_eventxprofiles() -> Tuple[Response, int]:
    """Get all eventxprofile associations."""
    try:
        stmt = select(EventXProfile)
        with Session(engine) as session:
            eventxprofiles = session.execute(stmt).scalars().all()
            data = [
                _serialize_eventxprofile(ep, include_id=True)
                for ep in eventxprofiles
            ]
        return build_response(StatusCode.OK, {"eventxprofiles": data})
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def get_eventxprofile_by_id(eventxprofileid: Any) -> Tuple[Response, int]:
    """Get a single event-profile association by ID."""
    validated_id = validate_id(eventxprofileid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return build_response(
            StatusCode.BAD_REQUEST,
            {"error": "Field 'eventxprofileid' must be an integer."},
        )

    try:
        with Session(engine) as session:
            eventxprofile = session.get(EventXProfile, validated_id)
            if not eventxprofile:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {
                        "error": f"""
                        EventXProfile with id {validated_id} not found.
                        """
                    },
                )
            return build_response(
                StatusCode.OK,
                _serialize_eventxprofile(eventxprofile, include_id=True),
            )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def create_eventxprofile(data: Any) -> Tuple[Response, int]:
    """Create a new eventxprofile association."""
    try:
        data = normalize_data(data)

        # Validate required fields
        required_fields = ["eventid", "profileid"]
        field_error = validate_required_fields(data, required_fields)
        if field_error is not None:
            missing = [
                field
                for field in required_fields
                if field not in data or not data[field]
            ]
            fields_str = "', '".join(missing)
            return build_response(
                StatusCode.BAD_REQUEST,
                {"error": f"Missing required fields: '{fields_str}'."},
            )

        # Validate integer IDs
        validated_ids, error = _validate_integer_ids(
            data, ["eventid", "profileid"]
        )
        if error:
            return build_response(StatusCode.BAD_REQUEST, error[0])

        eventid = validated_ids["eventid"]
        profileid = validated_ids["profileid"]

        # Check if event and profile exist
        with Session(engine) as session:
            event = session.get(Event, eventid)
            profile = session.get(Profile, profileid)

            if not event or not profile:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {"error": "Event or Profile not found."},
                )

            # Create the association
            eventxprofile = EventXProfile(eventid=eventid, profileid=profileid)
            session.add(eventxprofile)
            session.commit()
            session.refresh(eventxprofile)
            return build_response(
                StatusCode.CREATED,
                _serialize_eventxprofile(eventxprofile, include_id=True),
            )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )


def delete_eventxprofile(eventxprofileid: Any) -> Tuple[Response, int]:
    """Delete an eventxprofile association by ID."""
    validated_id = validate_id(eventxprofileid)
    if validated_id == StatusCode.BAD_REQUEST.value:
        return build_response(
            StatusCode.BAD_REQUEST,
            {"error": "Field 'eventxprofileid' must be an integer."},
        )

    try:
        with Session(engine) as session:
            eventxprofile = session.get(EventXProfile, validated_id)
            if not eventxprofile:
                return build_response(
                    StatusCode.NOT_FOUND,
                    {
                        "error": f"""
                        EventXProfile with id {validated_id} not found.
                        """
                    },
                )
            session.delete(eventxprofile)
            session.commit()
        return build_response(
            StatusCode.OK,
            {"message": f"EventXProfile {validated_id} deleted."},
        )
    except Exception as e:
        return build_response(
            StatusCode.INTERNAL_SERVER_ERROR, {"error": f"{str(e)}"}
        )
