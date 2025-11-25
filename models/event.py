from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[DateTime]
    start: Mapped[DateTime]
    end: Mapped[str]
    location: Mapped[str]
