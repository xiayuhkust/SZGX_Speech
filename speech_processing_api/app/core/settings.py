from functools import lru_cache
from .config import Settings

@lru_cache()  # 缓存设置，避免重复读取
def get_settings() -> Settings:
    return Settings()