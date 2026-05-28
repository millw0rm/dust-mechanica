from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field


class PhysicsMargins(BaseModel):
    model_config = ConfigDict(extra="allow")

    speed_headroom_ratio: float | None = None
    torque_margin: float | None = None
    efficiency_margin: float | None = None
    mass_budget_margin_kg: float | None = None


class PhysicsWarning(BaseModel):
    code: str
    message: str
    severity: str = Field(default="medium")


class PhysicsCheck(BaseModel):
    name: str
    status: str
    passed: bool
    margins: dict = Field(default_factory=dict)
    warnings: list[PhysicsWarning] = Field(default_factory=list)


class PhysicsRiskFlag(BaseModel):
    code: str
    message: str
    severity: str = Field(default="medium")


class PhysicsResult(BaseModel):
    status: str
    checks: list[PhysicsCheck] = Field(default_factory=list)
    margins: PhysicsMargins
    warnings: list[PhysicsWarning] = Field(default_factory=list)
    risk_flags: list[PhysicsRiskFlag] = Field(default_factory=list)

    @computed_field
    @property
    def passed(self) -> bool:
        return self.status != "fail"

    @computed_field
    @property
    def summary(self) -> str:
        return "pass_with_warnings" if self.status == "warning" else self.status

    def summary_payload(self) -> dict:
        return {
            "status": self.status,
            "checks": [check.model_dump() for check in self.checks],
            "margins": self.margins.model_dump(),
            "warnings": [warning.model_dump() for warning in self.warnings],
            "risk_flags": [flag.model_dump() for flag in self.risk_flags],
        }


# Backward-compatible import name used by older modules/tests.
PhysicsWarnings = PhysicsWarning
