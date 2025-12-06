from typing import Optional, Tuple
from utils.load_icon import _load_code_icons


def round_temperature(temp: Optional[float]) -> Optional[int]:
    return round(temp) if temp is not None else None


def round_temperatures(temps: list[float]) -> list[int]:
    return [round(temp) for temp in temps]


def weather_code_to_info(code: int) -> Tuple[Optional[str], Optional[str]]:
    code_data = _load_code_icons()
    code_str = str(code)
    info = code_data.get(code_str, {})
    if info:
        return info["icon"], info["label"]

    return None, None
