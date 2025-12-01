from sqlalchemy import select
from sqlalchemy.orm import Session
from models.event import Event
from models.profile import Profile
from models.event_profile import Event_Profile
from database.database import engine


def get_event_profiles():
    stmt = select(Event_Profile)
    with Session(engine) as session:
        event_profiles = session.execute(stmt).scalars().all()
        data = [
            {
                "profile_id": event_profile.profileid,
                "event_id": event_profile.eventid,
            }
            for event_profile in event_profiles
        ]
    return {"event_profiles": data}


def get_event_profile_by_id(event_profile_id):
    try:
        event_profile_id = int(event_profile_id)
    except Exception:
        return {"error": "'event_profile_id' must be an integer."}, 400
    try:
        with Session(engine) as session:
            event_profile = session.get(Event_Profile, event_profile_id)
            if not event_profile:
                return {"error": "Event_Profile not found."}, 404
            result = {
                "id": event_profile.id,
                "eventid": event_profile.eventid,
                "profileid": event_profile.profileid,
            }
        return result, 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def create_event_profile(data):
    # Accept both dict (API) and ImmutableMultiDict (form)
    if hasattr(data, "to_dict"):
        data = data.to_dict()

    required_fields = ["eventid", "profileid"]
    missing = [
        field
        for field in required_fields
        if field not in data or not data[field]
    ]
    if missing:
        return {"error": f"Missing required fields: {', '.join(missing)}"}, 400

    try:
        eventid = int(data["eventid"])
        profileid = int(data["profileid"])
    except Exception:
        return {"error": "'eventid' and 'profileid' must be integers."}, 400

    with Session(engine) as session:
        event = session.get(Event, eventid)
        profile = session.get(Profile, profileid)
        if not event or not profile:
            return {"error": "Event or Profile not found."}, 404

        event_profile = Event_Profile(eventid=eventid, profileid=profileid)
        session.add(event_profile)
        session.commit()
        session.refresh(event_profile)
        result = {
            "id": event_profile.id,
            "eventid": event_profile.eventid,
            "profileid": event_profile.profileid,
        }
    return result, 201


def delete_event_profile(event_profile_id):
    try:
        event_profile_id = int(event_profile_id)
    except Exception:
        return {"error": "'event_profile_id' must be an integer."}, 400

    with Session(engine) as session:
        event_profile = session.get(Event_Profile, event_profile_id)
        if not event_profile:
            return {"error": "Event_Profile not found."}, 404
        session.delete(event_profile)
        session.commit()
    return {"message": f"Event_Profile {event_profile_id} deleted."}, 200
