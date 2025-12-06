from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from models.db_models.base import Base


class EventXProfile(Base):
    __tablename__ = "eventxprofile"

    id: Mapped[int] = mapped_column(primary_key=True)
    eventid: Mapped[int] = mapped_column(
        ForeignKey("event.id"), nullable=False
    )
    profileid: Mapped[int] = mapped_column(
        ForeignKey("profile.id"), nullable=False
    )

    # Relationships
    event = relationship("Event", back_populates="eventxprofile")
    profile = relationship("Profile", back_populates="eventxprofile")
