from services.calendar_service import get_full_calendar
from datetime import datetime


class TestCalendarFlow:
    """Test the full calendar generation flow."""

    def test_get_full_calendar_current_month(self,
                                             mocker,
                                             sample_weather_code_data):
        """Test generating calendar for current month."""
        # Mock external dependencies
        mocker.patch('utils.converters._load_code_icons',
                     return_value=sample_weather_code_data)

        # Mock holiday API
        mocker.patch('api.holiday_api.fetch_public_holidays', return_value=[])

        # Mock weather API
        mocker.patch('api.weather_api.fetch_daily_forecast', return_value={
            "daily": {"time": [], "weather_code": []}
        })

        year, month = datetime.now().year, datetime.now().month
        result = get_full_calendar(year, month)

        assert result.year == year
        assert result.month == month
        assert len(result.weeks) > 0
        assert all(len(week.days) == 7 for week in result.weeks)
