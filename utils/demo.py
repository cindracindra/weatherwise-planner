"""Demo accounts: one fresh, throwaway calendar per "Try the demo" click.

Each demo account gets sample events placed around today's date, so the
calendar and today's timeline have something to show. Demo accounts are
deleted when their visitor signs out, or after DEMO_LIFETIME for visitors
who just leave, and there are never more than DEMO_CAP at once. Events go
with their account (ON DELETE CASCADE).
"""

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from database.engine import engine
from models.db_models.event import Event
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


def _at(day: datetime, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return day.replace(hour=hour, minute=minute)


def sample_events(user_id: int) -> list[Event]:
    """The sample events for a demo account, around today (London)."""
    t = get_today_detail()
    today = datetime(t["year"], t["month"], t["day"])
    events = []
    for offset, start, end, name, location in SAMPLE_EVENTS:
        day = today + timedelta(days=offset)
        events.append(Event(
            name=name, location=location, user_id=user_id,
            start_time=_at(day, start), end_time=_at(day, end),
        ))
    return events


def cleanup_demo_users(session: Session) -> None:
    """Delete demo accounts older than DEMO_LIFETIME, then the oldest
    beyond DEMO_CAP (leaving room for one more)."""
    cutoff = datetime.now() - DEMO_LIFETIME
    session.execute(
        delete(AppUser).where(AppUser.is_demo, AppUser.created_at < cutoff)
    )
    live = session.execute(
        select(func.count()).select_from(AppUser).where(AppUser.is_demo)
    ).scalar_one()
    extra = live - (DEMO_CAP - 1)
    if extra > 0:
        oldest = (
            select(AppUser.id).where(AppUser.is_demo)
            .order_by(AppUser.created_at).limit(extra)
        )
        session.execute(delete(AppUser).where(AppUser.id.in_(oldest)))


def create_demo_user() -> AppUser:
    """A brand-new demo account with sample events, after tidying up old
    ones. Nothing is shared between demo visitors."""
    with Session(engine) as session:
        cleanup_demo_users(session)
        user = AppUser(name=DEMO_NAME, is_demo=True)
        session.add(user)
        session.flush()  # gives the account its id for the events
        session.add_all(sample_events(user.id))
        session.commit()
        session.refresh(user)
        session.expunge(user)
        return user


def delete_demo_user(user_id: int) -> None:
    """Delete a demo account and its events. Real accounts are untouched,
    whatever id is passed."""
    with Session(engine) as session:
        session.execute(
            delete(AppUser).where(AppUser.id == user_id, AppUser.is_demo)
        )
        session.commit()
