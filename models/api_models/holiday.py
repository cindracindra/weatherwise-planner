from dataclasses import dataclass
from datetime import date

@dataclass
class Holiday:
    date: date
    local_name: str

    @classmethod
    def from_api_response(cls, data: dict) -> 'Holiday':
        return cls(
            date=date.fromisoformat(data.get("date")),
            local_name=data.get("localName")
        )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "local_name": self.local_name
        }