import calendar
from datetime import datetime, date
from nager import get_holidays
from weather import get_weather_icon_daily
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def _load_code_icons():
    with open("static/data/code_icon.json", "r") as f:
        return json.load(f)

def print_month_calendar(year, month):
    cal = calendar.Calendar(firstweekday=6)
    

    weeks = cal.monthdayscalendar(year, month)
    return weeks
    # has to be a matix because we know first, how many weeks, second, where does the day start in a week at the beginning of the month

# if __name__ == "__main__":
#     year = 2025
#     month = 11
#     month_calendar = print_month_calendar(year, month)
#     print(month_calendar)

def current_date():
    now = datetime.now()
    return now.year, now.month

def getDayToHighlight(year, month):
    now = datetime.now()
    # safety check, also checked in app.py already so redundant but whatever
    if now.year == year and now.month == month:
        return now.day
    return 0 # should this be 0 or None? question
    # find today's date to highlight if the month and year match

def generate_matrix(calendar_matrix, holidays_dict, year, month):
    holidays_matrix = []
    for week in calendar_matrix:
        week_data = []
        for day in week:
            cell = {"day": day, "holiday": [], "weather": {}}
            # again we could have a lightweight class call daycell instead of dict
            if day != 0:
                date_obj = date(year, month, day)
                cell["holiday"].extend(holidays_dict.get(date_obj, []))
            week_data.append(cell)
        holidays_matrix.append(week_data)
    # the return type is List[List[Dict]], good for rendering, not for lookup
    return holidays_matrix


def get_month_calendar_matrix(year, month):

    # get the calendar matrix in a format of [[0, 0, 1, 2, ...], [...], ...]
    calendar_matrix = print_month_calendar(year, month)

    holidays_dict = get_holidays(year=year, country_code="GB") # error handling here as it is an API call?

    calendar_holiday_matrix = generate_matrix(calendar_matrix, holidays_dict, year, month)
    
    return calendar_holiday_matrix

def weather_code_to_info(code, code_data):
    code_str = str(code) # is it needed to have error handling here?
    info = code_data.get(code_str)
    if info:
        return info['icon'], info['label']
        #return code_data.get(code_str)['icon'], code_data.get(code_str)['label']
        # what is the difference between .get and indexing directly?

    return None, None

def weather_code_info_week(weather_codes_dict):
    # a list, becasue we are not doing lookup but sequential access with order important
    # weather_info_week = []

    # load the code_icon.json file once
    code_data = _load_code_icons()

    for date, code in weather_codes_dict.items():
        icon, label = weather_code_to_info(code, code_data)
        weather_codes_dict[date] = {"code": code, "icon": icon, "label": label}
    return weather_codes_dict

    # groups = code_data['groups']
    # for code in weather_codes_dict.values():
    #     icon, label = weather_code_to_info(code, code_data)
    #     weather_info_week.append({"code": code, "icon": icon, "label": label})
    # return weather_info_week

def generate_matix_with_weather(calendar_holiday_matrix, weather_info_week_dict, year, month):
    # n = len(weather_info_week_dict)

    for week in calendar_holiday_matrix:
        # if i >= n:
            # return calendar_holiday_matrix
        for cell in week:
            if cell["day"]:
                date_str = f"{year:04d}-{month:02d}-{cell['day']:02d}"
                if date_str in weather_info_week_dict:
                    cell["weather"] = weather_info_week_dict[date_str]
    
    return calendar_holiday_matrix

def get_month_calendar_matrix_weather(year, month):
    # can do parallel API calls here if needed for performance
    calendar_holiday_matrix = get_month_calendar_matrix(year, month)

    weather_codes_dict_this_week = get_weather_icon_daily()

    weather_info_week_dict = weather_code_info_week(weather_codes_dict_this_week)

    calendar_weather_matrix = generate_matix_with_weather(calendar_holiday_matrix, weather_info_week_dict, year, month)
    
    return calendar_weather_matrix
#notes
# i can reconstruct the date with date(year, month, day(the integer))

# if __name__ == "__main__":
#     calendar_holiday_matrix = get_month_calendar_matrix_weather(2025, 12)
#     print(calendar_holiday_matrix)
#     weather_info_week = weather_code_info_week([3, 3, 61, 61, 63, 63, 80])
#     print(weather_info_week)
    # calendar_holiday_matrix = print_month_calendar(2024, 6)
    # print(calendar_holiday_matrix)