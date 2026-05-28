from fastapi import APIRouter
from packages.domain.schemas.requirements import RequirementInput
from packages.engineering.validation import validate_requirement

router = APIRouter(prefix="/v1/requirements", tags=["requirements"])


@router.post('/validate')
def validate(req: RequirementInput):
    result = validate_requirement(req)
    return {
        "normalized": result["normalized"].model_dump(),
        "issues": result["issues"],
        "missing": result["missing"],
        "conflicts": result["conflicts"],
        "risk_flags": [],
    }
