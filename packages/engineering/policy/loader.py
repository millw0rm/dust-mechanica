from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import yaml
from pydantic import BaseModel, Field


class RiskThresholds(BaseModel):
    low_margin_high: float = Field(gt=0)
    low_margin_medium: float = Field(gt=0)
    speed_headroom_factor: float = Field(gt=0)
    min_efficiency: float = Field(gt=0, le=1)


class WeightPerturbation(BaseModel):
    bound: float = Field(gt=0, le=0.5)
    samples: int = Field(ge=5, le=1000)


class Policy(BaseModel):
    version: str
    risk_thresholds: RiskThresholds
    topology_thresholds: dict[str, dict[str, float]] = Field(default_factory=dict)
    weight_perturbation: WeightPerturbation


@lru_cache(maxsize=4)
def load_policy(version: str = "v1") -> Policy:
    path = Path(__file__).parent / version / "scoring.yaml"
    data = yaml.safe_load(path.read_text())
    return Policy(**data)
