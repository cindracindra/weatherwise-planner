from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from models.db_models.base import Base
from models.db_models.user import AppUser  # noqa: F401  (registers app_user)


class Profile(Base):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    # The account that owns this profile. Optional until existing profiles
    # have been given an owner (see 001_accounts.sql).
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )

    eventxprofile = relationship("EventXProfile", back_populates="profile")
