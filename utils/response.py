"""
HTTP status codes and response utilities.

This module provides centralized HTTP status codes and standardized
response formatting for consistent API responses.
"""

from enum import Enum
from typing import Tuple
from flask import Response, jsonify


# Common HTTP Status Codes
class StatusCode(Enum):
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


# Status Message mappings
STATUS_MESSAGES = {
    StatusCode.OK: "SUCCESS",
    StatusCode.CREATED: "CREATED",
    StatusCode.BAD_REQUEST: "BAD_REQUEST",
    StatusCode.NOT_FOUND: "NOT_FOUND",
    StatusCode.INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
}


# Build Response Body
def build_response(status_code: StatusCode, data) -> Tuple[Response, int]:
    response_body = {
        "statusCode": status_code.value,
        "statusMessage": STATUS_MESSAGES[status_code],
        "data": data,
    }
    return jsonify(response_body), status_code.value
