from enum import Enum
from pydantic import BaseModel, Field


class Quantity(BaseModel):
    value: float
    unit: str


class Confidence(BaseModel):
    value: float = Field(0.5, ge=0.0, le=1.0)
    rationale: str = "placeholder"


class PriorityWeights(BaseModel):
    efficiency: float = 0.25
    cost: float = 0.25
    compactness: float = 0.2
    performance_margin: float = 0.3


class RiskSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RiskFlag(BaseModel):
    code: str
    message: str
    severity: RiskSeverity = RiskSeverity.medium


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    failed = "failed"
    completed = "completed"
    awaiting_review = "awaiting_review"
    approved = "approved"
    rejected = "rejected"
