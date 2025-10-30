from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn


class Settings(BaseSettings):
    token: str
    postgres_dsn: PostgresDsn
    db_user: str
    db_pass: str
    db_name: str
    redis_port: str
    openai_key: str
    post_generator: str
    semantic_layout_generator: str
    threads_generator: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
