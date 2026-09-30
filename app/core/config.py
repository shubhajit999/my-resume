from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ResumeForge"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "default_development_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    ALLOWED_ORIGINS: list[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "resumeforge_user"
    POSTGRES_PASSWORD: str = "resumeforge_password"
    POSTGRES_DB: str = "resumeforge_db"
    DATABASE_URL: str = "postgresql://resumeforge_user:resumeforge_password@localhost:5432/resumeforge_db"

    TEST_DATABASE_URL: str = "postgresql://resumeforge_user:resumeforge_password@localhost:5432/resumeforge_test_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
