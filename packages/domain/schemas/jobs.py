from pydantic import BaseModel
from packages.domain.schemas.common import JobStatus


class JobStatusResponse(BaseModel):
    id: str
    status: JobStatus
    progress: float
