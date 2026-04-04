from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic reads these automatically from the .env file
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_env: str = "development"
    secret_key: str

    database_url: str
    redis_url: str

    openai_api_key: str = ""

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    ses_sender_email: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Single instance imported everywhere — not re-read on every use
settings = Settings()