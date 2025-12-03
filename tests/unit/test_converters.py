from utils.converters import (
    weather_code_to_info,
    round_temperature,
    round_temperatures
)


class TestWeatherCodeToInfo:
    def test_valid_weather_code(self, mocker, sample_weather_code_data):
        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        icon, label = weather_code_to_info(61)

        assert icon == "rain.svg"
        assert label == "Rain"

    def test_invalid_weather_code(self, mocker, sample_weather_code_data):
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
        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        icon, label = weather_code_to_info(-1)

        assert icon is None
        assert label is None

    def test_zero_weather_code(self, mocker, sample_weather_code_data):
        mocker.patch(
            'utils.converters._load_code_icons',
            return_value=sample_weather_code_data
        )

        icon, label = weather_code_to_info(0)

        assert icon == "clear-day.svg"
        assert label == "Clear"


class TestRoundTemperature:
    def test_round_positive_temperature(self):
        assert round_temperature(15.7) == 16
        assert round_temperature(15.2) == 15

    def test_round_negative_temperature(self):
        assert round_temperature(-2.3) == -2
        assert round_temperature(-2.7) == -3

    def test_round_none_temperature(self):
        assert round_temperature(None) is None

    def test_round_zero_temperature(self):
        assert round_temperature(0.0) == 0


class TestRoundTemperatures:
    def test_round_multiple_temperatures(self):
        temps = [14.5, 15.2, 16.0, 15.8]
        rounded = round_temperatures(temps)
        assert rounded == [14, 15, 16, 16]

    def test_round_empty_list(self):
        temps = []
        rounded = round_temperatures(temps)
        assert rounded == []

    def test_round_negative_temperatures(self):
        temps = [-2.3, -2.7, -3.5]
        rounded = round_temperatures(temps)
        assert rounded == [-2, -3, -4]
