from pydantic import BaseModel


class Settings(BaseModel):
    api_env: str = "dev"
    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()
