from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    event_profile = relationship("Event_Profile", back_populates="profile")
