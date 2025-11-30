from sqlalchemy import select
from sqlalchemy.orm import Session
from models.event import Event
from database import engine


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
