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
