from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    start: Mapped[datetime]
    end: Mapped[datetime]
    location: Mapped[str]

    event_profile = relationship("Event_Profile", back_populates="event")
