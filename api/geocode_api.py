"""Address search for places: Nominatim (OpenStreetMap), within Greater
London.

Nominatim's usage policy asks for at most one request a second, an app
that says who it is, results that are cached, and no search-as-you-type.
So every search goes through this server (one shared pace and the app's
User-Agent), only when someone presses Search, and each query's results
are kept for a day.
"""

import logging
import threading
import time
from typing import Any, Dict, List

import requests

from config import Config

logger = logging.getLogger(__name__)

CACHE_FOR = 24 * 60 * 60   # seconds a query's results are kept
MIN_GAP = 1.0              # seconds between requests to Nominatim
MAX_RESULTS = 5
QUERY_MAX = 200

_cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}
_last = {"at": None}
_lock = threading.Lock()


class GeocodeError(Exception):
    """The search service couldn't be reached or answered badly."""


def reset_cache() -> None:
    """Forget cached searches and the last request time (for tests)."""
    _cache.clear()
    _last["at"] = None


def _wait_turn() -> None:
    """Keep requests at least MIN_GAP apart, across the whole app."""
    with _lock:
        now = time.monotonic()
        if _last["at"] is not None:
            wait = MIN_GAP - (now - _last["at"])
            if wait > 0:
                time.sleep(wait)
        _last["at"] = time.monotonic()


# Parts of a London address that say nothing on a London planner
OBVIOUS = {"Greater London", "England", "United Kingdom", "London"}


def _short(address: str) -> str:
    """'Royal Botanic Gardens, Kew, Kew, London Borough of Richmond upon
    Thames, Greater London, England, United Kingdom' -> 'Royal Botanic
    Gardens, Kew, London Borough of Richmond upon Thames'."""
    parts = []
    for part in (p.strip() for p in address.split(",")):
        if part and part not in OBVIOUS and part not in parts:
            parts.append(part)
    return ", ".join(parts[:4])


def _result(item: Dict[str, Any]) -> Dict[str, Any]:
    address = item.get("display_name", "")
    return {
        "name": item.get("name") or address.split(",")[0],
        "address": address,
        "short": _short(address),
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
    }


def search(query: str) -> List[Dict[str, Any]]:
    """Up to MAX_RESULTS places in Greater London matching the query, each
    {name, address, short (the address without the obvious), latitude,
    longitude}. Queries under 3 characters find
    nothing. Raises GeocodeError if the service fails."""
    query = " ".join((query or "").split())[:QUERY_MAX]
    if len(query) < 3:
        return []
    key = query.lower()
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_FOR:
        return cached[1]

    _wait_turn()
    try:
        response = requests.get(
            Config.NOMINATIM_URL,
            params={
                "q": query,
                "format": "jsonv2",
                "limit": MAX_RESULTS,
                "countrycodes": "gb",
                "viewbox": Config.LONDON_VIEWBOX,
                "bounded": 1,
            },
            headers={"User-Agent": Config.USER_AGENT,
                     "Accept-Language": "en-GB,en"},
            timeout=Config.API_TIMEOUT,
        )
        response.raise_for_status()
        results = [_result(item) for item in response.json()]
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        logger.warning("Address search failed: %s", e)
        raise GeocodeError(str(e)) from e
    _cache[key] = (time.monotonic(), results)
    return results
