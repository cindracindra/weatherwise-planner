"""
Weather data models for Open-Meteo API responses.

This module provides dataclasses for representing weather information
retrieved from the Open-Meteo API, including weather codes and readings.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherCode:
    """
    Represents a weather condition with its WMO code, icon, and label.

    Attributes:
        code: WMO weather code (0-99), None if unavailable
        icon: Path to weather icon SVG file, None if unavailable
        label: Human-readable weather description, None if unavailable

    Example:
        wc = WeatherCode(code=61, icon="rain.svg", label="Rain")
    """
    code: Optional[int]
    icon: Optional[str]
    label: Optional[str]

    def to_dict(self) -> dict:

        return {
            "code": self.code,
            "icon": self.icon,
            "label": self.label
        }


@dataclass
class WeatherReading:
    """
    Represents a weather measurement with temperature and conditions.

    Attributes:
        temperature: Temperature in Celsius (rounded), None if unavailable
        weather_code: WeatherCode object containing condition details
        rain_chance: Chance of rain in percent (0-100), None if unavailable

    """
    temperature: Optional[int]
    weather_code: WeatherCode
    rain_chance: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "weather_code": self.weather_code.to_dict(),
            "rain_chance": self.rain_chance,
        }
