from sqlalchemy.orm import relationship, Mapped, mapped_column

from models.db_models.base import Base


class Profile(Base):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    eventxprofile = relationship("EventXProfile", back_populates="profile")
