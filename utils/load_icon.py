from functools import lru_cache
import json
from config import Config


@lru_cache(maxsize=1)
def _load_code_icons():
    with open(Config.WEATHER_CODES_ICON_PATH, "r") as f:
        return json.load(f)
