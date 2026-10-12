from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from models.db_models.base import Base
from models.db_models.user import AppUser  # noqa: F401  (registers app_user)

# What a place can be; the form offers these in this order
CATEGORIES = [
    "park", "garden", "walk", "viewpoint", "market", "museum", "gallery",
    "cinema", "theatre", "café", "restaurant", "pub", "sport", "other",
]


class Place(Base):
    """Somewhere the account likes to go, and the weather it suits.

    A place suits any mix of sunny, cloudy and rainy days (all three means
    any weather; ticking rainy is how a place says it is indoors), and
    optionally only days whose temperature is within temp_min..temp_max.
    """

    __tablename__ = "place"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )
    name: Mapped[str]
    category: Mapped[str]
    address: Mapped[Optional[str]]
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    notes: Mapped[Optional[str]]
    suits_sunny: Mapped[bool] = mapped_column(default=True)
    suits_cloudy: Mapped[bool] = mapped_column(default=True)
    suits_rainy: Mapped[bool] = mapped_column(default=False)
    temp_min: Mapped[Optional[int]]
    temp_max: Mapped[Optional[int]]
    # How long a visit usually takes; sizes the suggested time window
    visit_minutes: Mapped[int] = mapped_column(default=120)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
