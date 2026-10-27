from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "校园快递收发系统"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "mysql+pymysql://campus:campus_pass@127.0.0.1:3306/"
        "campus_express?charset=utf8mb4"
    )
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    JWT_SECRET: str = "change_me_to_a_random_string_at_least_32_chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PICKUP_CODE_EXPIRE_DAYS: int = 7
    OVERDUE_THRESHOLD_DAYS: int = 3

    LOGIN_MAX_FAIL: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
