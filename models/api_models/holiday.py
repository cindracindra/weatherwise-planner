"""
Holiday data models for Nager.Date API responses.

This module provides dataclasses for representing public holiday information
retrieved from the Nager.Date API.
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class Holiday:
    """
    Represents a public holiday with its date and name.

    Attributes:
        date: The date of the holiday (Python date object)
        local_name: The holiday name in the local language

    """
    date: date
    local_name: str

    @classmethod
    def from_api_response(cls, data: dict) -> 'Holiday':
        """
        Create a Holiday object from raw Nager.Date API response.

        This factory method parses the API response and extracts only
        the fields needed by the application (date and localName).

        Args:
            data: Dictionary containing raw API response data with keys:
                  - date (str): ISO format date string (YYYY-MM-DD)
                  - localName (str): Holiday name in local language

        Returns:
            Holiday object with parsed date and local_name

        """
        return cls(
            date=date.fromisoformat(data.get("date")),
            local_name=data.get("localName")
        )

    def to_dict(self) -> dict:
        """
        Convert Holiday to JSON-serializable dictionary.
        """
        return {
            "date": self.date.isoformat(),
            "local_name": self.local_name
        }
