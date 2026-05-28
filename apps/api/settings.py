import os
from pydantic import BaseModel


class Settings(BaseModel):
    api_env: str = "dev"
    log_level: str = "INFO"
    sim_adapter_enabled: bool = True
    cad_adapter_enabled: bool = True


def get_settings() -> Settings:
    return Settings(
        sim_adapter_enabled=os.getenv("SIM_ADAPTER_ENABLED", "true").lower() == "true",
        cad_adapter_enabled=os.getenv("CAD_ADAPTER_ENABLED", "true").lower() == "true",
    )
