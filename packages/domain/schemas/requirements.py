
from pydantic import BaseModel, Field, AliasChoices
from packages.domain.schemas.common import PriorityWeights, Quantity


class FunctionalTargets(BaseModel):
    travel: Quantity
    max_speed: Quantity
    payload_mass: Quantity
    duty_cycle: float = Field(..., ge=0.0, le=1.0)
    backlash_tolerance_mm: float | None = Field(default=None, ge=0.0)
    precision_target_mm: float | None = Field(default=None, ge=0.0)


class Constraints(BaseModel):
    max_motor_power_w: float = Field(0.0, ge=0.0)
    max_total_mass_kg: float = Field(0.0, ge=0.0)


class RequirementInput(BaseModel):
    decision_objective: str = "balanced"
    topology: str = "belt-driven-linear-axis"
    functional_targets: FunctionalTargets
    constraints: Constraints
    priorities: PriorityWeights = Field(
        default_factory=PriorityWeights,
        validation_alias=AliasChoices("priorities", "optimization_priorities"),
    )
