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
    site_url: str
    site_host: str
    site_port: int
    merchant_login: str
    password1: str
    password2: str
    semantic_layout_generator: str
    threads_generator: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def get_webhook_url(self) -> str:
        """Динамически формирует путь для вебхука."""
        return f"{self.site_url}/webhook"


settings = Settings()
