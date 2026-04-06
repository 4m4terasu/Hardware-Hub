from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hardware Hub"
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"
    database_url: str = "sqlite:///./hardware_hub.db"

    jwt_secret_key: str = "change-me-in-local-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    bootstrap_admin_email: str = "admin@booksy.com"
    bootstrap_admin_password: str = "Admin123!"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()