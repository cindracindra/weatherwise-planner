from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from models.base import Base


class Event_Profile(Base):
    __tablename__ = "event_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    eventid: Mapped[int] = mapped_column(
        ForeignKey("event.id"), nullable=False
    )
    profileid: Mapped[int] = mapped_column(
        ForeignKey("profile.id"), nullable=False
    )

    # Relationships
    event = relationship("Event", back_populates="event_profile")
    profile = relationship("Profile", back_populates="event_profile")
