"""Demo accounts: one fresh, throwaway calendar per "Try the demo" click.

Each demo account gets sample events placed around today's date, so the
calendar and today's timeline have something to show, and sample places
so the suggestions do too. Demo accounts are
deleted when their visitor signs out, or after DEMO_LIFETIME for visitors
who just leave. At most DEMO_CAP exist at once: beyond that, new demos are
refused rather than evicting someone mid-visit. Events go with their
account (ON DELETE CASCADE).
"""

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from database.engine import engine
from models.db_models.event import Event
from models.db_models.place import Place
from models.db_models.user import AppUser
from services.datetime_service import get_today_detail

DEMO_NAME = "Demo visitor"
DEMO_LIFETIME = timedelta(days=1)
DEMO_CAP = 200

# (days from today, start, end, name, location)
SAMPLE_EVENTS = [
    (-2, "19:00", "22:00", "Dinner at Dishoom", "King's Cross"),
    (0, "08:15", "09:00", "Run along the canal", "Regent's Canal"),
    (0, "12:30", "13:30", "Lunch with Priya", "Borough Market"),
    (0, "19:00", "21:30", "Film night", "Prince Charles Cinema"),
    (1, "10:00", "10:45", "Dentist", "Marylebone"),
    (2, "14:00", "16:00", "Walk at Kew Gardens", "Kew Gardens"),
    (4, "18:30", "20:00", "Climbing session", "The Castle Climbing Centre"),
    (6, "11:00", "15:00", "Picnic in Hyde Park", "Hyde Park"),
    (9, "09:00", "17:00", "Design conference", "Barbican Centre"),
]


# (name, category, address, latitude, longitude, suits sunny, cloudy,
#  rainy, lowest °C, highest °C, visit minutes, notes)
SAMPLE_PLACES = [
    ("Hyde Park", "park", "Hyde Park, London W2", 51.5073, -0.1657,
     True, False, False, 14, None, 150, "Picnic by the Serpentine."),
    ("Kew Gardens", "garden", "Kew, Richmond TW9 3AE", 51.4787, -0.2956,
     True, True, False, 10, None, 180, "The glasshouses help if it turns."),
    ("Primrose Hill", "viewpoint", "Primrose Hill, London NW1", 51.5394,
     -0.1608, True, False, False, None, None, 60, "Best near sunset."),
    ("Regent's Canal", "walk", "Little Venice to Camden Lock", 51.5226,
     -0.1830, True, True, False, 8, None, 120, None),
    ("Borough Market", "market", "8 Southwark Street, London SE1 1TL",
     51.5055, -0.0910, True, True, True, None, None, 90, "Mostly covered."),
    ("British Museum", "museum", "Great Russell Street, London WC1B 3DG",
     51.5194, -0.1270, False, False, True, None, None, 150, None),
    ("Tate Modern", "gallery", "Bankside, London SE1 9TG", 51.5076,
     -0.0994, False, True, True, None, None, 120, "Free; the Turbine Hall."),
    ("Prince Charles Cinema", "cinema", "7 Leicester Place, London WC2H 7BY",
     51.5113, -0.1302, False, False, True, None, None, 150, None),
]


def sample_places(user_id: int) -> list[Place]:
    """The sample places for a demo account."""
    return [
        Place(user_id=user_id, name=name, category=category, address=address,
              latitude=lat, longitude=lng, suits_sunny=sunny,
              suits_cloudy=cloudy, suits_rainy=rainy, temp_min=low,
              temp_max=high, visit_minutes=minutes, notes=notes)
        for (name, category, address, lat, lng, sunny, cloudy, rainy, low,
             high, minutes, notes) in SAMPLE_PLACES
    ]


def _at(day: datetime, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return day.replace(hour=hour, minute=minute)


def sample_events(user_id: int, place_ids: dict | None = None
                  ) -> list[Event]:
    """The sample events for a demo account, around today (London). An
    event at one of the sample places is linked to it (place_ids maps a
    place's name to its id)."""
    place_ids = place_ids or {}
    t = get_today_detail()
    today = datetime(t["year"], t["month"], t["day"])
    events = []
    for offset, start, end, name, location in SAMPLE_EVENTS:
        day = today + timedelta(days=offset)
        events.append(Event(
            name=name, location=location, user_id=user_id,
            start_time=_at(day, start), end_time=_at(day, end),
            place_id=place_ids.get(location),
        ))
    return events


class DemoFull(Exception):
    """DEMO_CAP demo accounts are already in use."""


def cleanup_demo_users(session: Session) -> int:
    """Delete demo accounts older than DEMO_LIFETIME, and return how many
    are still live. The age is measured with the database's own clock,
    the same one that set created_at."""
    session.execute(
        delete(AppUser).where(
            AppUser.is_demo,
            AppUser.created_at < func.now() - DEMO_LIFETIME,
        )
    )
    return session.execute(
        select(func.count()).select_from(AppUser).where(AppUser.is_demo)
    ).scalar_one()


def create_demo_user() -> AppUser:
    """A brand-new demo account with sample events, after tidying up old
    ones. Nothing is shared between demo visitors. Raises DemoFull when
    DEMO_CAP demos are live."""
    with Session(engine) as session:
        if cleanup_demo_users(session) >= DEMO_CAP:
            session.commit()  # keep the tidy-up
            raise DemoFull()
        user = AppUser(name=DEMO_NAME, is_demo=True)
        session.add(user)
        session.flush()  # gives the account its id for the rest
        places = sample_places(user.id)
        session.add_all(places)
        session.flush()  # gives the places their ids for the events
        session.add_all(sample_events(
            user.id, {p.name: p.id for p in places}))
        session.commit()
        session.refresh(user)
        session.expunge(user)
        return user


def delete_demo_user(user_id: int) -> None:
    """Delete a demo account with its events and places. Real accounts
    are untouched, whatever id is passed."""
    with Session(engine) as session:
        session.execute(
            delete(AppUser).where(AppUser.id == user_id, AppUser.is_demo)
        )
        session.commit()
