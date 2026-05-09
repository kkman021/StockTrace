from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://radar:changeme@db:5432/etf_radar"
    REDIS_URL: str = "redis://redis:6379/0"
    CRAWLER_URL: str = "http://crawler:8001"

    DEFAULT_BREADTH_THRESHOLD: float = 0.6
    DEFAULT_DEPTH_THRESHOLD: float = 0.6
    DEFAULT_CONSECUTIVE_DAYS: int = 3
    DEFAULT_SLIDING_WINDOW: int = 5
    DEFAULT_REDUCTION_BREADTH_THRESHOLD: float = 0.6
    DEFAULT_REDUCTION_CONSECUTIVE_DAYS: int = 3


settings = Settings()
