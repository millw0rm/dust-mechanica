from fastapi import APIRouter
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.schemas.responses import ValidationResponse
from packages.engineering.validation import validate_requirement

router = APIRouter(prefix="/v1/requirements", tags=["requirements"])


@router.post('/validate', response_model=ValidationResponse)
def validate(req: RequirementInput):
    result = validate_requirement(req)
    return ValidationResponse(
        normalized=result["normalized"].model_dump(),
        issues=result["issues"],
        missing=result["missing"],
        conflicts=result["conflicts"],
    )
