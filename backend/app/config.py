from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    # JWT
    jwt_secret: str = "CHANGE_ME"  # overwrite in .env
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()
