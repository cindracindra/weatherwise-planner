import calendar
from datetime import datetime
from zoneinfo import ZoneInfo

from config import Config


def get_today_detail():
    # Use the forecast's timezone rather than the server clock (UTC on Render)
    now = datetime.now(ZoneInfo(Config.TIMEZONE))

    today_detail = {
        "day": int(now.day),
        "month": int(now.month),
        "year": int(now.year),
        "hour": int(now.hour),
        "day_name": calendar.day_name[now.weekday()],
        "month_name": calendar.month_name[now.month],
    }

    return today_detail
