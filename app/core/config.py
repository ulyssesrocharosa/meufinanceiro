from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "dev-only-secret-change-before-production"
    database_url: str = "sqlite:///./data/financas.db"
    admin_email: str = "admin@minhasfinancas.com"
    admin_password: str = ""
    session_https_only: bool = False
    run_scheduler: bool = True
    evolution_api_url: str = ""
    evolution_api_key: str = ""
    evolution_instance: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def validate_runtime_settings() -> None:
    """Reject unsafe settings when the application is exposed publicly."""
    if settings.app_env.lower() != "production":
        return
    if settings.secret_key == "dev-only-secret-change-before-production" or len(settings.secret_key) < 32:
        raise RuntimeError("SECRET_KEY deve ter ao menos 32 caracteres em produção.")
    if settings.admin_password and len(settings.admin_password) < 12:
        raise RuntimeError("ADMIN_PASSWORD deve ter ao menos 12 caracteres em produção.")
