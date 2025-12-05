"""Unit tests for utils/converters.py - weather code conversion and temperature rounding."""

from utils.converters import (
    weather_code_to_info,
    round_temperature,
    round_temperatures
)


class TestWeatherCodeToInfo:
    """Test weather code to icon/label conversion."""

    def test_valid_weather_code(self, mocker, sample_weather_code_data):
        """Test converting a valid weather code (61) to icon and label."""
        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        icon, label = weather_code_to_info(61)

        assert icon == "rain.svg"
        assert label == "Rain"

    def test_invalid_weather_code(self, mocker, sample_weather_code_data):
        """Test that invalid weather code (999) returns None values."""
        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        icon, label = weather_code_to_info(999)

        assert icon is None
        assert label is None

    def test_invalid_weather_code_negative(self,
                                           mocker,
                                           sample_weather_code_data):
        """Test that negative weather code returns None values."""
        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        icon, label = weather_code_to_info(-1)

        assert icon is None
        assert label is None

    def test_zero_weather_code(self, mocker, sample_weather_code_data):
        """Test weather code 0 (clear sky) converts correctly."""
        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        icon, label = weather_code_to_info(0)

        assert icon == "clear-day.svg"
        assert label == "Clear"


class TestRoundTemperature:
    """Test single temperature rounding."""

    def test_round_positive_temperature(self):
        """Test rounding positive temperatures."""
        assert round_temperature(15.7) == 16
        assert round_temperature(15.2) == 15

    def test_round_negative_temperature(self):
        """Test rounding negative temperatures."""
        assert round_temperature(-2.3) == -2
        assert round_temperature(-2.7) == -3

    def test_round_none_temperature(self):
        """Test that None temperature returns None."""
        assert round_temperature(None) is None

    def test_round_zero_temperature(self):
        """Test rounding zero temperature."""
        assert round_temperature(0.0) == 0


class TestRoundTemperatures:
    """Test batch temperature rounding."""

    def test_round_multiple_temperatures(self):
        """Test rounding a list of temperatures."""
        temps = [14.5, 15.2, 16.0, 15.8]
        rounded = round_temperatures(temps)
        assert rounded == [14, 15, 16, 16]

    def test_round_empty_list(self):
        """Test that empty list returns empty list."""
        temps = []
        rounded = round_temperatures(temps)
        assert rounded == []

    def test_round_negative_temperatures(self):
        """Test rounding a list of negative temperatures."""
        temps = [-2.3, -2.7, -3.5]
        rounded = round_temperatures(temps)
        assert rounded == [-2, -3, -4]
