from pydantic import BaseModel, Field


class PhysicsMargins(BaseModel):
    speed_headroom_ratio: float
    torque_margin: float
    efficiency_margin: float
    mass_budget_margin_kg: float


class PhysicsWarnings(BaseModel):
    code: str
    message: str
    severity: str = Field(default="medium")


class PhysicsResult(BaseModel):
    passed: bool
    summary: str
    margins: PhysicsMargins
    warnings: list[PhysicsWarnings] = Field(default_factory=list)
