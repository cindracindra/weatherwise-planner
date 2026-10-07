from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from models.db_models.base import Base


class AppUser(UserMixin, Base):
    """A person who signs in. Named app_user because "user" is reserved.

    UserMixin adds what Flask-Login needs: is_authenticated, get_id(), ...
    """

    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Google's permanent account ID ("sub"); None for demo accounts
    google_sub: Mapped[Optional[str]] = mapped_column(unique=True)
    email: Mapped[Optional[str]]
    name: Mapped[str]
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
