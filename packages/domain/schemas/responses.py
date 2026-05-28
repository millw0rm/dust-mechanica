
from pydantic import BaseModel, Field
from packages.domain.schemas.candidate import Candidate
from packages.domain.schemas.common import JobStatus


class ValidationResponse(BaseModel):
    schema_version: str = "2.0"
    normalized: dict
    issues: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class CandidateGenerationResponse(BaseModel):
    schema_version: str = "2.0"
    candidates: list[Candidate]
    issues: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    assumptions: dict
    policy_version: str = "v1"
    topology_selection_trace: dict = Field(default_factory=dict)
    topology_candidate_stats: dict = Field(default_factory=dict)


class JobDetailResponse(BaseModel):
    schema_version: str = "2.0"
    id: str
    status: JobStatus
    progress: float
    created_at: str
    updated_at: str
    completed_at: str | None = None
    error: str | None = None
    result: CandidateGenerationResponse | None = None
    review: dict | None = None
    report: dict | None = None


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    reviewer_id: str | None = None
    source_id: str | None = None
    context_tag: str | None = None
    observed_at: str
    achieved_motion: bool = True
    achieved_force: bool = True
    achieved_pressure: bool = True
    notes: str = ""


class TelemetrySliceMetrics(BaseModel):
    period_start: str
    topology: str
    policy_version: str
    artifact_version: str
    total_feedback: int
    avg_rating: float
    motion_success_rate: float
    force_success_rate: float
    pressure_success_rate: float


class TelemetrySlicesResponse(BaseModel):
    schema_version: str = "2.1"
    bucket: str
    slices: list[TelemetrySliceMetrics] = Field(default_factory=list)


class TelemetryDriftMetric(BaseModel):
    metric: str
    baseline: float
    recent: float
    delta: float


class TelemetryDriftResponse(BaseModel):
    schema_version: str = "2.1"
    baseline_days: int
    recent_days: int
    baseline_start: str
    baseline_end: str
    recent_start: str
    recent_end: str
    sample_sizes: dict
    metrics: list[TelemetryDriftMetric] = Field(default_factory=list)
