from functools import lru_cache
import json

@lru_cache(maxsize=1)
def _load_code_icons():
    with open("../static/data/code_icon.json", "r") as f:
        return json.load(f)