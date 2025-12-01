from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherCode:
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
    temperature: Optional[int]
    weather_code: WeatherCode

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "weather_code": self.weather_code.to_dict()
        }
