from sqlalchemy.orm import relationship, Mapped, mapped_column

from models.base import Base


class Profile(Base):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    event_profile = relationship("Event_Profile", back_populates="profile")
