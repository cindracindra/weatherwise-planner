from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Event_Profile(Base):
    __tablename__ = "event_profile"

    eventid: Mapped[int] = mapped_column(ForeignKey("event.id"), nullable=False)
    profileid: Mapped[int] = mapped_column(ForeignKey("profile.id"), nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="event_profile")
    profile: Mapped["Profile"] = relationship(back_populates="event_profile")
