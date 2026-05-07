from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "sqlite:///./data/financas.db"
    admin_email: str = "admin@financas.com"
    admin_password: str = "admin123"
    evolution_api_url: str = ""
    evolution_api_key: str = ""
    evolution_instance: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
