from pydantic import BaseModel, Field, ConfigDict


class PhysicsMargins(BaseModel):
    model_config = ConfigDict(extra="allow")

    speed_headroom_ratio: float | None = None
    torque_margin: float | None = None
    efficiency_margin: float | None = None
    mass_budget_margin_kg: float | None = None


class PhysicsWarnings(BaseModel):
    code: str
    message: str
    severity: str = Field(default="medium")


class PhysicsResult(BaseModel):
    passed: bool
    summary: str
    margins: PhysicsMargins
    warnings: list[PhysicsWarnings] = Field(default_factory=list)
