from datetime import datetime
from typing import Any, Dict
from utils.response import StatusCode


def normalize_data(data: Any) -> Dict[str, Any]:
    if hasattr(data, "to_dict"):
        return data.to_dict()
    return data


def validate_id(id: Any) -> int | StatusCode:
    try:
        return int(id)
    except (ValueError, TypeError):
        return StatusCode.BAD_REQUEST.value


def validate_required_fields(
    data: Dict[str, Any], required_fields: list
) -> None | StatusCode:

    missing = [
        field
        for field in required_fields
        if field not in data or not data[field]
    ]
    if missing:
        return StatusCode.BAD_REQUEST.value
    return None


def parse_datetime(value: str) -> datetime | StatusCode:
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError, AttributeError):
        return StatusCode.BAD_REQUEST.value


def validate_datetime_range(
    start_time: datetime, end_time: datetime
) -> None | StatusCode:

    if end_time <= start_time:
        return StatusCode.BAD_REQUEST.value
    return None
