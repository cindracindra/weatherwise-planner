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
