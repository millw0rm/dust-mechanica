from pydantic import BaseModel, Field
from packages.domain.schemas.common import Confidence, RiskFlag


class Components(BaseModel):
    motor_id: str
    drive_id: str
    transmission_id: str


class Performance(BaseModel):
    achievable_speed_mps: float = Field(..., ge=0.0)
    torque_margin: float
    est_efficiency: float = Field(..., ge=0.0, le=1.0)
    est_total_mass_kg: float = Field(..., ge=0.0)


class ScoreDimension(BaseModel):
    raw_metric: float
    normalized_metric: float
    applied_weight: float
    weighted_contribution: float


class ScoreBreakdown(BaseModel):
    total: float
    efficiency: ScoreDimension
    cost: ScoreDimension
    compactness: ScoreDimension
    performance_margin: ScoreDimension
    lead_time_impact: ScoreDimension | None = None
    sourcing_risk: ScoreDimension | None = None
    engineering_fit: ScoreDimension | None = None


class Robustness(BaseModel):
    level: str
    volatility_index: float


class Candidate(BaseModel):
    simulation_summary: dict | None = None
    cad_artifact_ref: dict | None = None
    id: str
    components: Components
    performance: Performance
    score_breakdown: ScoreBreakdown
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    confidence: Confidence = Field(default_factory=Confidence)
    feasible: bool = True
    robustness: Robustness | None = None
