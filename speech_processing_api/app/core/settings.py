from functools import lru_cache
from .config import settings

@lru_cache()
def get_settings():
    return settings
