import pytest
from models.api_models.weather import WeatherCode, WeatherReading
from models.api_models.calendar import CalendarDay, CalendarWeek, CalendarMonth


class TestWeatherCode:
    def test_weather_code_creation(self):
        wc = WeatherCode(code=61, icon="rain.svg", label="Rain")

        assert wc.code == 61
        assert wc.icon == "rain.svg"
        assert wc.label == "Rain"

    def test_weather_code_to_dict(self):
        wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
        wc_dict = wc.to_dict()

        assert wc_dict == {
            "code": 61,
            "icon": "rain.svg",
            "label": "Rain"
        }


class TestCalendarDay:
    def test_calendarDay_creation(self):
        day = CalendarDay(day=15, holidays=["Holiday1", "Holiday2"])
        assert day.day == 15
        assert day.holidays == ["Holiday1", "Holiday2"]
        assert day.weather is None

    def test_is_empty_property(self):

        empty_day = CalendarDay(day=0)
        non_empty_day = CalendarDay(day=15)

        assert empty_day.is_empty is True
        assert non_empty_day.is_empty is False

    def test_is_holiday_property(self):

        holiday_day = CalendarDay(day=25, holidays=["Christmas"])
        non_holiday_day = CalendarDay(day=15, holidays=[])

        assert holiday_day.is_holiday is True
        assert non_holiday_day.is_holiday is False


class TestCalendarWeek:
    def test_calendar_week_valid(self):
        """Test creating a valid CalendarWeek."""
        days = [CalendarDay(day=i) for i in range(7)]
        week = CalendarWeek(days=days)

        assert len(week.days) == 7

    def test_calendar_week_invalid_length(self):
        """Test CalendarWeek with wrong number of days."""
        days = [CalendarDay(day=i) for i in range(5)]

        with pytest.raises(ValueError, match="exactly 7 days"):
            CalendarWeek(days=days)


class TestWeatherReading:
    """Test WeatherReading model."""
    def test_weather_reading_creation(self):
        """Test creating a WeatherReading."""
        wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
        wr = WeatherReading(temperature=15, weather_code=wc)

        assert wr.temperature == 15
        assert wr.weather_code.code == 61
        assert wr.weather_code.icon == "rain.svg"
        assert wr.weather_code.label == "Rain"

    def test_weather_reading_to_dict(self):
        """Test converting WeatherReading to dict."""
        wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
        wr = WeatherReading(temperature=15, weather_code=wc)
        result = wr.to_dict()

        assert result == {
            "temperature": 15,
            "weather_code": {
                "code": 61,
                "icon": "rain.svg",
                "label": "Rain"
            }
        }

    def test_weather_reading_with_none_temperature(self):
        """Test WeatherReading with None temperature."""
        wc = WeatherCode(code=61, icon="🌧️", label="Light rain")
        wr = WeatherReading(temperature=None, weather_code=wc)

        assert wr.temperature is None
        assert wr.weather_code.code == 61

    def test_weather_reading_with_none_weather_code(self):
        """Test WeatherReading with None weather code values."""
        wc = WeatherCode(code=None, icon=None, label=None)
        wr = WeatherReading(temperature=15, weather_code=wc)

        assert wr.temperature == 15
        assert wr.weather_code.code is None
        assert wr.weather_code.icon is None
        assert wr.weather_code.label is None


class TestCalendarMonth:

    def test_calendar_month_creation(self):
        """Test creating a CalendarMonth."""
        # Create a simple week
        days = [CalendarDay(day=i) for i in range(7)]
        week = CalendarWeek(days=days)

        # Create a month with one week
        month = CalendarMonth(
            year=2025,
            month=12,
            weeks=[week],
            current_day=15
        )

        assert month.year == 2025
        assert month.month == 12
        assert len(month.weeks) == 1
        assert month.current_day == 15

    def test_calendar_month_default_current_day(self):
        """Test CalendarMonth with default current_day."""
        days = [CalendarDay(day=i) for i in range(7)]
        week = CalendarWeek(days=days)

        month = CalendarMonth(
            year=2025,
            month=12,
            weeks=[week]
        )

        assert month.current_day == 0  # Default value

    def test_calendar_month_to_dict(self):
        """Test converting CalendarMonth to dict."""
        # Create days with various properties
        days = [
            CalendarDay(day=0),  # Empty day
            CalendarDay(day=1),
            CalendarDay(day=2),
            CalendarDay(day=3),
            CalendarDay(day=4),
            CalendarDay(day=5),
            CalendarDay(day=6)
        ]
        week = CalendarWeek(days=days)

        month = CalendarMonth(
            year=2025,
            month=12,
            weeks=[week],
            current_day=15
        )

        result = month.to_dict()

        assert result["year"] == 2025
        assert result["month"] == 12
        assert result["current_day"] == 15
        assert len(result["weeks"]) == 1
        assert len(result["weeks"][0]) == 7

    def test_calendar_month_with_holidays_and_weather(self):
        """Test CalendarMonth with holidays and weather data."""
        wc = WeatherCode(code=61, icon="rain.svg", label="Rain")

        days = [
            CalendarDay(day=0),
            CalendarDay(day=1),
            CalendarDay(day=2),
            CalendarDay(day=3),
            CalendarDay(day=4),
            CalendarDay(day=5, holidays=["Bank Holiday"], weather=wc),
            CalendarDay(day=6)
        ]
        week = CalendarWeek(days=days)

        month = CalendarMonth(
            year=2025,
            month=12,
            weeks=[week],
            current_day=5
        )

        # Check the day with holiday and weather
        assert month.weeks[0].days[5].day == 5
        assert month.weeks[0].days[5].holidays == ["Bank Holiday"]
        assert month.weeks[0].days[5].weather.code == 61
        assert month.weeks[0].days[5].weather.icon == "rain.svg"

    def test_calendar_month_multiple_weeks(self):
        """Test CalendarMonth with multiple weeks."""
        weeks = []
        for _ in range(5):  # 5 weeks in the month
            days = [CalendarDay(day=j) for j in range(7)]
            weeks.append(CalendarWeek(days=days))

        month = CalendarMonth(
            year=2025,
            month=12,
            weeks=weeks,
            current_day=0
        )

        assert len(month.weeks) == 5
        assert all(len(week.days) == 7 for week in month.weeks)
