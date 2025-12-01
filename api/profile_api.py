from sqlalchemy import select
from sqlalchemy.orm import Session
from models.profile import Profile
from database.database import engine


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


def get_profile_by_id(profile_id):
    try:
        profile_id = int(profile_id)
    except Exception:
        return {"error": "'profile_id' must be an integer."}, 400
    try:
        with Session(engine) as session:
            profile = session.get(Profile, profile_id)
            if not profile:
                return {"error": "Profile not found."}, 404
            result = {
                "id": profile.id,
                "name": profile.name,
            }
        return result, 200
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}, 500


def create_profile(data):
    # Accept both dict (API) and ImmutableMultiDict (form)
    if hasattr(data, "to_dict"):
        data = data.to_dict()

    required_fields = ["name"]
    missing = [
        field
        for field in required_fields
        if field not in data or not data[field]
    ]
    if missing:
        return {"error": f"Missing required fields: {', '.join(missing)}"}, 400

    # Create profile
    with Session(engine) as session:
        profile = Profile(name=data["name"])
        session.add(profile)
        session.commit()
        session.refresh(profile)
        result = {
            "id": profile.id,
            "name": profile.name,
        }
    return result, 201


def delete_profile(profile_id):
    try:
        profile_id = int(profile_id)
    except Exception:
        return {"error": "'profile_id' must be an integer."}, 400

    with Session(engine) as session:
        profile = session.get(Profile, profile_id)
        if not profile:
            return {"error": "Profile not found."}, 404
        session.delete(profile)
        session.commit()
    return {"message": f"Profile {profile_id} deleted."}, 200
