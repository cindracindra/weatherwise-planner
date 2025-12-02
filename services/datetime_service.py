import calendar
from datetime import datetime

def get_today_detail():
    now = datetime.now()
    
    today_detail = {
        "day": now.day,
        "month": now.month,
        "year": now.year,
        "day_name": calendar.day_name[now.weekday()],
        "month_name": calendar.month_name[now.month],
    }
    
    return today_detail
