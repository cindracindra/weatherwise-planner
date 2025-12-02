from sqlalchemy import select
from sqlalchemy.orm import Session
from models.event import Event
from database.database import engine


def get_events():
    try:
        stmt = select(Event)
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
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def get_event_by_id(event_id):
    try:
        event_id = int(event_id)
    except Exception:
        return {"error": "'event_id' must be an integer."}, 400
    try:
        with Session(engine) as session:
            event = session.get(Event, event_id)
            if not event:
                return {"error": "Event not found."}, 404
            result = {
                "id": event.id,
                "name": event.name,
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
                "location": event.location,
            }
        return result, 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def create_event(data):

    try:
        # Accept both dict (API) and ImmutableMultiDict (form)
        if hasattr(data, "to_dict"):
            data = data.to_dict()

        required_fields = ["name", "start_time", "end_time", "location"]
        missing = [
            field
            for field in required_fields
            if field not in data or not data[field]
        ]
        if missing:
            return {
                "error": f"Missing required fields: {', '.join(missing)}"
            }, 400

        # Validate datetime fields
        from datetime import datetime

        try:
            start_time_dt = datetime.fromisoformat(data["start_time"])
            end_time_dt = datetime.fromisoformat(data["end_time"])
        except Exception:
            return {
                "error": "'start_time' and 'end_time' must be valid "
                "ISO datetime strings."
            }, 400

        if end_time_dt < start_time_dt:
            return {"error": "'end_time' must be after 'start_time'."}, 400

        # Create event
        with Session(engine) as session:
            event = Event(
                name=data["name"],
                start_time=start_time_dt,
                end_time=end_time_dt,
                location=data["location"],
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            result = {
                "id": event.id,
                "name": event.name,
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
                "location": event.location,
            }
        return result, 201
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def update_event(event_id, data):
    try:
        event_id = int(event_id)
    except Exception:
        return {"error": "'event_id' must be an integer."}, 400

    try:
        # Accept both dict (API) and ImmutableMultiDict (form)
        if hasattr(data, "to_dict"):
            data = data.to_dict()

        with Session(engine) as session:
            event = session.get(Event, event_id)
            if not event:
                return {"error": "Event not found."}, 404

            # Validate datetime fields if provided
            from datetime import datetime

            if "start_time" in data and data["start_time"]:
                try:
                    start_time_dt = datetime.fromisoformat(data["start_time"])
                    event.start_time = start_time_dt
                except Exception:
                    return {
                        "error": "'start_time' must be a valid ISO datetime."
                    }, 400

            if "end_time" in data and data["end_time"]:
                try:
                    end_time_dt = datetime.fromisoformat(data["end_time"])
                    event.end_time = end_time_dt
                except Exception:
                    return {
                        "error": "'end_time' must be a valid ISO datetime."
                    }, 400

            # Validate end_time is after start_time
            if event.end_time < event.start_time:
                return {"error": "'end_time' must be after 'start_time'."}, 400

            # Update other fields
            if "name" in data and data["name"]:
                event.name = data["name"]
            if "location" in data and data["location"]:
                event.location = data["location"]

            session.commit()
            session.refresh(event)
            result = {
                "id": event.id,
                "name": event.name,
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
                "location": event.location,
            }
        return result, 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def delete_event(event_id):
    try:
        event_id = int(event_id)
    except Exception:
        return {"error": "'event_id' must be an integer."}, 400

    try:
        with Session(engine) as session:
            event = session.get(Event, event_id)
            if not event:
                return {"error": "Event not found."}, 404
            session.delete(event)
            session.commit()
        return {"message": f"Event {event_id} deleted."}, 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500
