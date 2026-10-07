"""Whose calendar a request is for.

TEMPORARY (accounts step 2): sign-in does not exist yet, so every request
belongs to one local developer account. Step 3 replaces this with the
signed-in user from the session.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.engine import engine
from models.db_models.user import AppUser

DEV_SUB = "local-dev"


def current_user_id() -> int:
    """The id of the local developer account, created on first use."""
    with Session(engine) as session:
        user = session.execute(
            select(AppUser).where(AppUser.google_sub == DEV_SUB)
        ).scalar_one_or_none()
        if user is None:
            user = AppUser(google_sub=DEV_SUB, name="Local developer")
            session.add(user)
            session.commit()
        return user.id
