from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from models.db_models.base import Base
from models.db_models.user import AppUser  # noqa: F401  (registers app_user)

EVERY_DAY = "0123456"  # Monday is 0, as in date.weekday()


class UserSettings(Base):
    """How an account wants suggestions. An account without a row uses
    the defaults below.

    suggest_days lists the weekdays to suggest for, as digits (Monday 0 to
    Sunday 6). The hours are the window searched for good weather: on
    weekdays after work, at weekends most of the day.
    """

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    # One row per account at most
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), unique=True
    )
    suggest_days: Mapped[str] = mapped_column(default=EVERY_DAY)
    weekday_start: Mapped[int] = mapped_column(default=18)
    weekday_end: Mapped[int] = mapped_column(default=21)
    weekend_start: Mapped[int] = mapped_column(default=9)
    weekend_end: Mapped[int] = mapped_column(default=18)
    skip_busy_days: Mapped[bool] = mapped_column(default=False)
    show_today: Mapped[bool] = mapped_column(default=True)
