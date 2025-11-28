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
    username=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
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
