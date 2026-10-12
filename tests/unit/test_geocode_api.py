"""Address search: Nominatim within London, paced and cached as its
usage policy asks."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from api import geocode_api
from api.geocode_api import GeocodeError, search
from config import Config

FOUND = [{
    "name": "Royal Botanic Gardens, Kew", "lat": "51.4781974", "lon": "-0.2968861",
    "display_name": "Royal Botanic Gardens, Kew, Kew, London Borough of "
                    "Richmond upon Thames, Greater London, England, United Kingdom",
}]


@pytest.fixture(autouse=True)
def fresh():
    geocode_api.reset_cache()
    yield
    geocode_api.reset_cache()


def response(json=None, status=200):
    r = MagicMock()
    r.json.return_value = json
    r.raise_for_status.side_effect = (
        requests.HTTPError(f"{status} Error") if status >= 400 else None)
    return r


def test_search_asks_for_london_only_and_says_who_we_are():
    with patch("api.geocode_api.requests.get", return_value=response(FOUND)) as get:
        results = search("Kew Gardens")
    params = get.call_args.kwargs["params"]
    assert params["viewbox"] == Config.LONDON_VIEWBOX and params["bounded"] == 1
    assert params["countrycodes"] == "gb"
    assert get.call_args.kwargs["headers"]["User-Agent"] == Config.USER_AGENT
    assert results == [{
        "name": "Royal Botanic Gardens, Kew",
        "address": FOUND[0]["display_name"],
        "short": "Royal Botanic Gardens, Kew, London Borough of Richmond upon Thames",
        "latitude": 51.4781974, "longitude": -0.2968861,
    }]


def test_the_same_search_is_asked_once():
    with patch("api.geocode_api.requests.get", return_value=response(FOUND)) as get:
        search("Kew Gardens")
        search("  kew   GARDENS ")
    get.assert_called_once()


def test_short_queries_find_nothing_without_asking():
    with patch("api.geocode_api.requests.get") as get:
        assert search("ke") == [] and search("") == []
    get.assert_not_called()


def test_requests_are_a_second_apart():
    with patch("api.geocode_api.requests.get", return_value=response([])), \
         patch("api.geocode_api.time.sleep") as sleep:
        search("Hyde Park")
        search("Regent's Park")
    waited = sleep.call_args[0][0]
    assert 0 < waited <= geocode_api.MIN_GAP


@pytest.mark.parametrize("failure", [
    {"side_effect": requests.Timeout("slow")},
    {"return_value": response(status=429)},
    {"return_value": response(json=[{"name": "no coordinates"}])},
])
def test_failures_are_a_geocode_error_and_not_cached(failure):
    with patch("api.geocode_api.requests.get", **failure):
        with pytest.raises(GeocodeError):
            search("Kew Gardens")
    assert geocode_api._cache == {}
