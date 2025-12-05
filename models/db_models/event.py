from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from models.db_models.base import Base


class Event(Base):
    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    location: Mapped[str]

    eventxprofile = relationship("EventXProfile", back_populates="event")
