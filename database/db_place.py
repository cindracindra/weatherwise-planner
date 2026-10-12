"""Places: somewhere an account likes to go, and the weather it suits.

Like events, every function takes the id of the account the request is
for, and a place that belongs to someone else is treated exactly like one
that does not exist.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from flask import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.engine import engine
from models.db_models.place import CATEGORIES, Place
from utils.request import normalize_data, validate_id
from utils.response import StatusCode, build_response

logger = logging.getLogger(__name__)

NAME_MAX = 60
ADDRESS_MAX = 200
NOTES_MAX = 500
TEMP_RANGE = (-30, 50)        # °C a place's range may use
VISIT_RANGE = (15, 12 * 60)   # minutes a visit may last
TRUE_WORDS = {"1", "true", "on", "yes"}
WEATHER_FIELDS = ("suits_sunny", "suits_cloudy", "suits_rainy")


def serialize_place(place: Place) -> Dict[str, Any]:
    return {
        "id": place.id,
        "name": place.name,
        "category": place.category,
        "address": place.address,
        "latitude": place.latitude,
        "longitude": place.longitude,
        "notes": place.notes,
        "suits_sunny": place.suits_sunny,
        "suits_cloudy": place.suits_cloudy,
        "suits_rainy": place.suits_rainy,
        "temp_min": place.temp_min,
        "temp_max": place.temp_max,
        "visit_minutes": place.visit_minutes,
    }


def _bad_request(message: str) -> Tuple[Response, int]:
    return build_response(StatusCode.BAD_REQUEST, {"error": message})


def _not_found(placeid: int) -> Tuple[Response, int]:
    return build_response(
        StatusCode.NOT_FOUND, {"error": f"Place with id {placeid} not found."}
    )


def _server_error() -> Tuple[Response, int]:
    """Details go to the server log only, as for events."""
    logger.exception("Place request failed")
    return build_response(
        StatusCode.INTERNAL_SERVER_ERROR,
        {"error": "Something went wrong on our side. Please try again."},
    )


def owned_place(session: Session, placeid: int, user_id: int
                ) -> Optional[Place]:
    """The place if it exists and belongs to user_id, else None."""
    place = session.get(Place, placeid)
    if place is None or place.user_id != user_id:
        return None
    return place


# ---------- Validation ----------

def _flag(value: Any) -> bool:
    """A tick box from a form ("on") or a JSON boolean."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in TRUE_WORDS


def _text(value: Any) -> Optional[str]:
    text = str(value).strip() if value is not None else ""
    return text or None


def _int(value: Any, label: str, low: int, high: int) -> int:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a whole number.")
    if not low <= number <= high:
        raise ValueError(f"{label} must be between {low} and {high}.")
    return number


def _float(value: Any, label: str, low: float, high: float) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.")
    if not low <= number <= high:
        raise ValueError(f"{label} must be between {low} and {high}.")
    return number


def clean_place(data: Dict[str, Any], current: Optional[Place] = None
                ) -> Dict[str, Any]:
    """The place's fields from posted data, checked. For an update
    (`current` given), fields not in the data keep their value. Raises
    ValueError with a message fit to show the person."""
    def given(key):
        return key in data

    def now(key):
        return getattr(current, key) if current is not None else None

    fields: Dict[str, Any] = {}

    name = _text(data.get("name")) if given("name") else now("name")
    if not name:
        raise ValueError("Give the place a name.")
    if len(name) > NAME_MAX:
        raise ValueError(f"Keep the name to {NAME_MAX} characters.")
    fields["name"] = name

    category = (
        _text(data.get("category")) if given("category")
        else now("category")
    )
    if category not in CATEGORIES:
        raise ValueError("Choose a category from the list.")
    fields["category"] = category

    for key, limit, label in (("address", ADDRESS_MAX, "address"),
                              ("notes", NOTES_MAX, "notes")):
        value = _text(data.get(key)) if given(key) else now(key)
        if value and len(value) > limit:
            raise ValueError(f"Keep the {label} to {limit} characters.")
        fields[key] = value

    # An HTML form leaves unticked boxes out, so the page's form sends
    # weather_form and a missing box there means unticked. JSON callers
    # send only what they change; a new place defaults to dry weather.
    form_post = given("weather_form")
    defaults = {"suits_sunny": True, "suits_cloudy": True,
                "suits_rainy": False}
    for key in WEATHER_FIELDS:
        if given(key):
            fields[key] = _flag(data[key])
        elif form_post:
            fields[key] = False
        elif current is None:
            fields[key] = defaults[key]
        else:
            fields[key] = now(key)
    weather = WEATHER_FIELDS
    if not any(fields[k] for k in weather):
        raise ValueError("Tick at least one kind of weather the place suits.")

    for key, label in (("temp_min", "Lowest temperature"),
                       ("temp_max", "Highest temperature")):
        if given(key):
            raw = _text(data.get(key))
            fields[key] = _int(raw, label, *TEMP_RANGE) if raw else None
        else:
            fields[key] = now(key)
    if (fields["temp_min"] is not None and fields["temp_max"] is not None
            and fields["temp_min"] > fields["temp_max"]):
        raise ValueError(
            "The lowest temperature must not be above the highest.")

    if given("visit_minutes") and _text(data.get("visit_minutes")):
        fields["visit_minutes"] = _int(
            data["visit_minutes"], "Visit length", *VISIT_RANGE)
    else:
        fields["visit_minutes"] = now("visit_minutes") or 120

    # A pin is both coordinates or neither
    if given("latitude") or given("longitude"):
        lat, lng = _text(data.get("latitude")), _text(data.get("longitude"))
        if bool(lat) != bool(lng):
            raise ValueError("A map pin needs both latitude and longitude.")
        fields["latitude"] = _float(lat, "Latitude", -90, 90) if lat else None
        fields["longitude"] = (
            _float(lng, "Longitude", -180, 180) if lng else None)
    else:
        fields["latitude"] = now("latitude")
        fields["longitude"] = now("longitude")

    return fields


# ---------- Reading ----------

def list_places(user_id: int) -> list[Place]:
    """The account's places by name, detached from the session. Raises on
    a database failure; pages that show places handle it."""
    with Session(engine) as session:
        places = session.execute(
            select(Place).where(Place.user_id == user_id)
            .order_by(Place.name)
        ).scalars().all()
        session.expunge_all()
        return list(places)


def get_places(user_id: int) -> Tuple[Response, int]:
    try:
        data = [serialize_place(p) for p in list_places(user_id)]
        return build_response(StatusCode.OK, {"places": data})
    except Exception:
        return _server_error()


def get_place_by_id(placeid: Any, user_id: int) -> Tuple[Response, int]:
    validated = validate_id(placeid)
    if validated == StatusCode.BAD_REQUEST.value:
        return _bad_request("'placeid' must be an integer.")
    try:
        with Session(engine) as session:
            place = owned_place(session, validated, user_id)
            if not place:
                return _not_found(validated)
            return build_response(StatusCode.OK, serialize_place(place))
    except Exception:
        return _server_error()


# ---------- Changing ----------

def create_place(data: Any, user_id: int) -> Tuple[Response, int]:
    try:
        fields = clean_place(normalize_data(data or {}))
    except ValueError as e:
        return _bad_request(str(e))
    try:
        with Session(engine) as session:
            place = Place(user_id=user_id, **fields)
            session.add(place)
            session.commit()
            session.refresh(place)
            return build_response(StatusCode.CREATED, serialize_place(place))
    except Exception:
        return _server_error()


def update_place(placeid: Any, data: Any, user_id: int
                 ) -> Tuple[Response, int]:
    validated = validate_id(placeid)
    if validated == StatusCode.BAD_REQUEST.value:
        return _bad_request("'placeid' must be an integer.")
    try:
        with Session(engine) as session:
            place = owned_place(session, validated, user_id)
            if not place:
                return _not_found(validated)
            try:
                fields = clean_place(normalize_data(data or {}), place)
            except ValueError as e:
                return _bad_request(str(e))
            for key, value in fields.items():
                setattr(place, key, value)
            session.commit()
            session.refresh(place)
            return build_response(StatusCode.OK, serialize_place(place))
    except Exception:
        return _server_error()


def delete_place(placeid: Any, user_id: int) -> Tuple[Response, int]:
    """Delete one of the account's places. Events made from it stay, no
    longer linked to it."""
    validated = validate_id(placeid)
    if validated == StatusCode.BAD_REQUEST.value:
        return _bad_request("'placeid' must be an integer.")
    try:
        with Session(engine) as session:
            place = owned_place(session, validated, user_id)
            if not place:
                return _not_found(validated)
            session.delete(place)
            session.commit()
        return build_response(
            StatusCode.OK, {"message": f"Place {validated} deleted."})
    except Exception:
        return _server_error()
