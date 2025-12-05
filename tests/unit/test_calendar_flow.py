"""Integration tests for calendar generation flow - combines holidays, weather, and calendar matrix."""

from services.calendar_service import get_full_calendar
from datetime import datetime


class TestCalendarFlow:
    """Test the full calendar generation pipeline from services/calendar_service.py."""

    def test_get_full_calendar_current_month(self,
                                             mocker,
                                             sample_weather_code_data):
        """Test complete calendar generation with mocked APIs for current month."""
        # Mock weather code icon loading
        mocker.patch('utils.converters._load_code_icons',
                     return_value=sample_weather_code_data)

        # Mock holiday API to return no holidays
        mocker.patch('api.holiday_api.fetch_public_holidays', return_value=[])

        # Mock weather API to return empty forecast
        mocker.patch('api.weather_api.fetch_daily_forecast', return_value={
            "daily": {"time": [], "weather_code": []}
        })

        year, month = datetime.now().year, datetime.now().month
        result = get_full_calendar(year, month)

        # Verify calendar structure
        assert result.year == year
        assert result.month == month
        assert len(result.weeks) > 0
        assert all(len(week.days) == 7 for week in result.weeks)
