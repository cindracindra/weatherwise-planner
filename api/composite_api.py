from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from models.event import Event
from models.event_profile import Event_Profile
from models.profile import Profile
from database.database import engine


def get_events_by_profile_id(profile_id):
    stmt = (
        select(Event)
        .join(Event.event_profile)
        .where(Event_Profile.profileid == profile_id)
        .options(joinedload(Event.event_profile).joinedload(Event_Profile.profile))
    )
    with Session(engine) as session:
        events = session.execute(stmt).scalars().unique().all()
        data = [
            {
                "id": event.id,
                "name": event.name,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "location": event.location,
            }
            for event in events
        ]
    return {"events": data}
