from dataclasses import dataclass
import uuid


@dataclass
class CADAdapterV1:
    def build(self, model_input: dict) -> dict:
        artifact_id = f"cad-{uuid.uuid4()}"
        return {
            "adapter_version": "cad-v1",
            "artifact_id": artifact_id,
            "artifact_uri": f"artifact://cad/{artifact_id}",
            "component_manifest": model_input.get("components", {}),
            "mounting_dimensions": model_input.get("mounting_dimensions", {"shaft_diameter_mm": None, "bolt_pattern_mm": None}),
            "envelope": model_input.get("envelope", {"assumed_max_envelope_mm": [None, None, None], "missing_dimensions": ["mounting_depth_mm"]}),
        }
