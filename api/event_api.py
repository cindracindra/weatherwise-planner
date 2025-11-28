import os
from sqlalchemy import create_engine, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from models.event import Event
from models.profile import Profile
from models.event_profile import Event_Profile

# Load environment variables
load_dotenv()

url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    host=os.getenv("PGHOST"),
    port=int(os.getenv("PGPORT", "5432")),
    database=os.getenv("PGDATABASE"),
    query={"client_encoding": "utf8"},
)

engine = create_engine(url)


def get_events():
    stmt = select(Event)
    with Session(engine) as session:
        events = session.execute(stmt).scalars().unique().all()
        data = [
            {
                "id": event.id,
                "name": event.name,
                "start": event.start,
                "end": event.end,
                "location": event.location,
            }
            for event in events
        ]
    return {"events": data}


def create_event(data):

    # Accept both dict (API) and ImmutableMultiDict (form)
    if hasattr(data, "to_dict"):
        data = data.to_dict()

    required_fields = ["name", "start", "end", "location"]
    missing = [
        field
        for field in required_fields
        if field not in data or not data[field]
    ]
    if missing:
        return {"error": f"Missing required fields: {', '.join(missing)}"}, 400

    # Validate datetime fields
    from datetime import datetime

    try:
        start_dt = datetime.fromisoformat(data["start"])
        end_dt = datetime.fromisoformat(data["end"])
    except Exception:
        return {
            "error": "'start' and 'end' must be valid ISO datetime strings."
        }, 400

    if end_dt < start_dt:
        return {"error": "'end' must be after 'start'."}, 400

    # Create event
    with Session(engine) as session:
        event = Event(
            name=data["name"],
            start=start_dt,
            end=end_dt,
            location=data["location"],
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        result = {
            "id": event.id,
            "name": event.name,
            "start": event.start.isoformat(),
            "end": event.end.isoformat(),
            "location": event.location,
        }
    return result, 201


def get_profiles():
    stmt = select(Profile)
    with Session(engine) as session:
        profiles = session.execute(stmt).scalars().unique().all()
        data = [
            {
                "id": profile.id,
                "name": profile.name,
            }
            for profile in profiles
        ]
    return {"profiles": data}


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


def create_event_profile(data):
    pass
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

    # TODO: check if event/profile exist

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


def delete_event(event_id):
    try:
        event_id = int(event_id)
    except Exception:
        return {"error": "'event_id' must be an integer."}, 400

    with Session(engine) as session:
        event = session.get(Event, event_id)
        if not event:
            return {"error": "Event not found."}, 404
        session.delete(event)
        session.commit()
    return {"message": f"Event {event_id} deleted."}, 200


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
