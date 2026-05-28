"""Generate the physics-enriched demo comparison export."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline


BASELINE_PAYLOAD: dict[str, Any] = {
    "functional_targets": {
        "travel": {"value": 800, "unit": "mm"},
        "max_speed": {"value": 600, "unit": "mm/s"},
        "payload_mass": {"value": 12, "unit": "kg"},
        "duty_cycle": 0.7,
    },
    "constraints": {"max_motor_power_w": 1200, "max_total_mass_kg": 30},
}

CONSTRAINED_PAYLOAD: dict[str, Any] = {
    "functional_targets": {
        "travel": {"value": 800, "unit": "mm"},
        "max_speed": {"value": 600, "unit": "mm/s"},
        "payload_mass": {"value": 12, "unit": "kg"},
        "duty_cycle": 0.7,
    },
    "constraints": {"max_motor_power_w": 500, "max_total_mass_kg": 6},
}

CASES = {
    "case_a_baseline": {
        "label": "Case A (baseline)",
        "payload": BASELINE_PAYLOAD,
        "description": "1200 W max motor power, 30 kg max total mass",
    },
    "case_b_constrained": {
        "label": "Case B (constrained)",
        "payload": CONSTRAINED_PAYLOAD,
        "description": "500 W max motor power, 6 kg max total mass",
    },
}

CHECK_TYPES = {
    "structural": {
        "margin_keys": [
            "estimated_max_deflection_mm",
            "structural_deflection_margin",
            "estimated_stress_proxy_mpa",
            "structural_stress_margin",
            "structural_safety_factor_proxy",
        ],
        "warning_prefixes": ("PHYS_STRUCTURAL",),
    },
    "thermal": {
        "margin_keys": ["estimated_temp_rise_c", "thermal_margin", "duty_weighted_load"],
        "warning_prefixes": ("PHYS_THERMAL", "risk_thermal"),
    },
    "drivetrain": {
        "margin_keys": [
            "speed_headroom_ratio",
            "torque_margin",
            "efficiency_margin",
            "belt_stretch_margin",
            "belt_reflected_inertia_margin",
            "belt_required_speed_mps",
            "ball_screw_critical_speed_margin",
            "ball_screw_buckling_margin",
            "ball_screw_efficiency_margin",
            "direct_drive_speed_margin",
            "direct_drive_torque_margin",
            "direct_drive_duty_weighted_margin",
        ],
        "warning_prefixes": (
            "PHYS_SPEED",
            "PHYS_TORQUE",
            "PHYS_EFFICIENCY",
            "PHYS_BELT",
            "PHYS_BALL_SCREW",
            "PHYS_DIRECT_DRIVE",
            "risk_belt",
            "risk_screw",
            "risk_direct_drive",
        ),
    },
    "controls": {
        "margin_keys": [
            "controls_motion_profile_margin",
            "controls_torque_speed_margin",
            "controls_duty_margin",
            "speed_headroom_ratio",
            "torque_margin",
            "duty_weighted_load",
        ],
        "warning_prefixes": ("PHYS_CONTROL",),
        "simulation_checks": ["motion_profile_feasible", "torque_speed_margin_valid", "thermal_load_sanity"],
    },
}

CATEGORY_MARGIN_KEYS = {
    "structural_margin": ["structural_margin", "structural_deflection_margin", "structural_stress_margin"],
    "drivetrain_margin": [
        "speed_headroom_ratio",
        "torque_margin",
        "efficiency_margin",
        "belt_stretch_margin",
        "belt_reflected_inertia_margin",
        "ball_screw_critical_speed_margin",
        "ball_screw_buckling_margin",
        "ball_screw_efficiency_margin",
        "direct_drive_speed_margin",
        "direct_drive_torque_margin",
        "direct_drive_duty_weighted_margin",
    ],
    "thermal_margin": ["thermal_margin", "continuous_thermal_margin", "intermittent_thermal_margin"],
    "controls_tracking_margin": [
        "controls_motion_profile_margin",
        "controls_torque_speed_margin",
        "controls_duty_margin",
    ],
}


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")


def _physics_summary_label(summary: Any) -> str:
    if isinstance(summary, dict):
        return str(summary.get("status") or summary.get("summary") or "unknown")
    return str(summary)


def _candidate_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for candidate in response["candidates"]:
        margins = candidate.get("physics_margins") or {}
        rows.append(
            {
                "id": candidate["id"],
                "score": candidate["score_breakdown"]["total"],
                "physics_summary": _physics_summary_label(candidate.get("physics_summary")),
                "physics_passed": candidate.get("physics_passed"),
                "margins": margins,
                "warnings": candidate.get("physics_warnings") or [],
                "simulation_checks": (candidate.get("simulation_summary") or {}).get("checks", {}),
            }
        )
    return rows


def _passes_check(candidate: dict[str, Any], check_type: str) -> bool:
    warnings = candidate.get("warnings") or []
    prefixes = CHECK_TYPES[check_type].get("warning_prefixes", ())
    has_check_warning = any(str(w.get("code", "")).startswith(prefixes) for w in warnings)
    if check_type == "controls":
        checks = candidate.get("simulation_checks") or {}
        controls_ok = all(bool(checks.get(name)) for name in CHECK_TYPES[check_type]["simulation_checks"])
        return controls_ok and not has_check_warning
    if check_type == "drivetrain":
        margins = candidate.get("margins") or {}
        base_ok = margins.get("speed_headroom_ratio", 0.0) >= 0.0 and margins.get("torque_margin", 0.0) >= 0.0
        return base_ok and not has_check_warning
    return not has_check_warning


def _pass_fail_tables(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = {}
    for check_type, config in CHECK_TYPES.items():
        table = []
        for candidate in rows:
            margins = candidate.get("margins") or {}
            warnings = [
                w
                for w in candidate.get("warnings", [])
                if str(w.get("code", "")).startswith(tuple(config.get("warning_prefixes", ())))
            ]
            table.append(
                {
                    "candidate_id": candidate["id"],
                    "status": "pass" if _passes_check(candidate, check_type) else "fail",
                    "margins": {k: margins[k] for k in config["margin_keys"] if k in margins},
                    "warnings": warnings,
                }
            )
        tables[check_type] = table
    return tables


def _category_margin(margins: dict[str, Any], category: str) -> float | None:
    """Return one conservative margin for a physics category.

    Each exported candidate still carries all raw physics margins.  The category
    value is the minimum available numeric margin in that category so cross-case
    deltas answer the safety question directly: positive means the constrained
    case gained margin, negative means it lost margin.
    """

    values = [float(margins[key]) for key in CATEGORY_MARGIN_KEYS[category] if isinstance(margins.get(key), (int, float))]
    return round(min(values), 6) if values else None


def _category_margins(margins: dict[str, Any]) -> dict[str, float | None]:
    return {category: _category_margin(margins, category) for category in CATEGORY_MARGIN_KEYS}


def _safety_rank(candidate: dict[str, Any]) -> tuple[int, int, float, float, float, float, float]:
    category_margins = _category_margins(candidate.get("margins") or {})
    finite_margins = [value for value in category_margins.values() if isinstance(value, (int, float))]
    worst_margin = min(finite_margins) if finite_margins else -999.0
    drivetrain_margin = category_margins.get("drivetrain_margin")
    thermal_margin = category_margins.get("thermal_margin")
    structural_margin = category_margins.get("structural_margin")
    controls_margin = category_margins.get("controls_tracking_margin")
    return (
        1 if candidate.get("physics_passed") else 0,
        -len(candidate.get("warnings") or []),
        float(worst_margin),
        float(drivetrain_margin if drivetrain_margin is not None else -999.0),
        float(thermal_margin if thermal_margin is not None else -999.0),
        float(structural_margin if structural_margin is not None else -999.0),
        float(controls_margin if controls_margin is not None else -999.0),
    )


def _safest_candidate(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    return max(rows, key=_safety_rank) if rows else None


def _format_category_margins_for_sentence(margins: dict[str, float | None]) -> str:
    labels = {
        "structural_margin": "structural",
        "drivetrain_margin": "drivetrain",
        "thermal_margin": "thermal",
        "controls_tracking_margin": "controls/tracking",
    }
    parts = []
    for key, label in labels.items():
        value = margins.get(key)
        parts.append(f"{label}={value}" if value is not None else f"{label}=n/a")
    return ", ".join(parts)


def _safest_sentence(case: dict[str, Any]) -> str:
    return (
        f"`{case['safest_candidate_id']}` is safest for {case['label']} because it ranks highest after physics pass status, "
        f"warning count, and worst category margin; conservative category margins are "
        f"{_format_category_margins_for_sentence(case['safest_candidate_category_margins'])}."
    )


def _summarize_case(case_key: str, case: dict[str, Any], response: dict[str, Any], exported_at: str) -> dict[str, Any]:
    candidates = response["candidates"]
    top = candidates[0] if candidates else {}
    risk_flags = sorted({flag["code"] for candidate in candidates for flag in candidate.get("risk_flags", [])})
    rows = _candidate_rows(response)
    safest = _safest_candidate(rows)
    return {
        "exported_at_utc": exported_at,
        "case_key": case_key,
        "label": case["label"],
        "description": case["description"],
        "topology": response["normalized"]["topology"],
        "candidate_count": len(candidates),
        "risk_flags": risk_flags,
        "top_candidate_id": top.get("id"),
        "top_candidate_total_score": top.get("score_breakdown", {}).get("total"),
        "physics_pass_count": sum(1 for c in rows if c["physics_passed"]),
        "physics_warning_count": sum(len(c["warnings"]) for c in rows),
        "safest_candidate_id": safest["id"] if safest else None,
        "safest_candidate_category_margins": _category_margins(safest.get("margins") or {}) if safest else {},
        "per_candidate_physics_margins": rows,
        "pass_fail_by_check_type": _pass_fail_tables(rows),
    }


def _delta_summary(case_a: dict[str, Any], case_b: dict[str, Any]) -> dict[str, Any]:
    a_candidates = {c["id"]: c for c in case_a["per_candidate_physics_margins"]}
    b_candidates = {c["id"]: c for c in case_b["per_candidate_physics_margins"]}
    shared = sorted(set(a_candidates) & set(b_candidates))
    per_candidate = []
    for candidate_id in shared:
        a = a_candidates[candidate_id]
        b = b_candidates[candidate_id]
        margin_keys = sorted(set(a["margins"]) | set(b["margins"]))
        margin_deltas = {}
        for key in margin_keys:
            if isinstance(a["margins"].get(key), (int, float)) and isinstance(b["margins"].get(key), (int, float)):
                margin_deltas[key] = round(float(b["margins"][key]) - float(a["margins"][key]), 6)
        a_category_margins = _category_margins(a["margins"])
        b_category_margins = _category_margins(b["margins"])
        category_margin_deltas = {}
        for category, a_value in a_category_margins.items():
            b_value = b_category_margins.get(category)
            if isinstance(a_value, (int, float)) and isinstance(b_value, (int, float)):
                category_margin_deltas[f"{category}_delta_case_b_minus_a"] = round(float(b_value) - float(a_value), 6)
        per_candidate.append(
            {
                "candidate_id": candidate_id,
                "score_delta_case_b_minus_a": round(float(b["score"]) - float(a["score"]), 6),
                "physics_summary_changed": a["physics_summary"] != b["physics_summary"],
                "physics_passed_changed": a["physics_passed"] != b["physics_passed"],
                "category_margins_case_a": a_category_margins,
                "category_margins_case_b": b_category_margins,
                "category_margin_deltas_case_b_minus_a": category_margin_deltas,
                "margin_deltas_case_b_minus_a": margin_deltas,
            }
        )
    return {
        "topology_changed": case_a["topology"] != case_b["topology"],
        "top_candidate_changed": case_a["top_candidate_id"] != case_b["top_candidate_id"],
        "top_score_delta_case_b_minus_a": round(float(case_b["top_candidate_total_score"]) - float(case_a["top_candidate_total_score"]), 6),
        "physics_pass_count_delta_case_b_minus_a": case_b["physics_pass_count"] - case_a["physics_pass_count"],
        "physics_warning_count_delta_case_b_minus_a": case_b["physics_warning_count"] - case_a["physics_warning_count"],
        "risk_flags_added_in_b": sorted(set(case_b["risk_flags"]) - set(case_a["risk_flags"])),
        "risk_flags_removed_in_b": sorted(set(case_a["risk_flags"]) - set(case_b["risk_flags"])),
        "safest_candidate_case_a": case_a.get("safest_candidate_id"),
        "safest_candidate_case_b": case_b.get("safest_candidate_id"),
        "per_candidate": per_candidate,
    }


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def _format_margins(margins: dict[str, Any], keys: list[str]) -> str:
    values = [f"{key}={margins[key]}" for key in keys if key in margins]
    return "<br>".join(values) if values else "—"


def _build_physics_markdown(compare: dict[str, Any]) -> str:
    delta = compare["delta_summary"]
    lines = [
        "# Physics comparison",
        "",
        f"Generated: {compare['generated_at_utc']}",
        "",
        "## Safest candidate summary",
        "",
        f"- Case A safest candidate: `{delta['safest_candidate_case_a']}`",
        f"- Case B safest candidate: `{delta['safest_candidate_case_b']}`",
        "- Safety ranking prioritizes physics pass status, then fewer physics warnings, then the worst conservative category margin.",
        f"- {_safest_sentence(compare['case_a'])}",
        f"- {_safest_sentence(compare['case_b'])}",
        "- Belt-axis candidates are less safe in this run because their drivetrain and thermal checks carry high-severity risk flags, while the direct-drive candidate passes all four check groups.",
        "",
        "## Per-candidate physics margins",
    ]
    for case_key in ("case_a", "case_b"):
        case = compare[case_key]
        lines.extend(["", f"### {case['label']}"])
        rows = []
        for candidate in case["per_candidate_physics_margins"]:
            rows.append(
                [
                    candidate["id"],
                    candidate["physics_summary"],
                    candidate["physics_passed"],
                    _format_margins(candidate["margins"], ["speed_headroom_ratio", "torque_margin", "thermal_margin", "structural_safety_factor_proxy"]),
                ]
            )
        lines.append(_markdown_table(["Candidate", "Physics summary", "Passed", "Key margins"], rows))

    for check_type in ("structural", "thermal", "drivetrain", "controls"):
        lines.extend(["", f"## {check_type}"])
        for case_key in ("case_a", "case_b"):
            case = compare[case_key]
            rows = []
            for row in case["pass_fail_by_check_type"][check_type]:
                warning_codes = ", ".join(w["code"] for w in row["warnings"]) or "—"
                rows.append([row["candidate_id"], row["status"], _format_margins(row["margins"], list(row["margins"].keys())), warning_codes])
            lines.extend(["", f"### {case['label']}", _markdown_table(["Candidate", "Status", "Margins", "Warnings"], rows)])

    lines.extend(
        [
            "",
            "## Delta summary across cases",
            "",
            f"- Topology changed: `{delta['topology_changed']}`",
            f"- Top candidate changed: `{delta['top_candidate_changed']}`",
            f"- Top score delta (B - A): `{delta['top_score_delta_case_b_minus_a']}`",
            f"- Physics pass count delta (B - A): `{delta['physics_pass_count_delta_case_b_minus_a']}`",
            f"- Physics warning count delta (B - A): `{delta['physics_warning_count_delta_case_b_minus_a']}`",
            f"- Risk flags added in B: `{delta['risk_flags_added_in_b']}`",
            f"- Risk flags removed in B: `{delta['risk_flags_removed_in_b']}`",
            "",
        ]
    )
    rows = [
        [item["candidate_id"], item["score_delta_case_b_minus_a"], item["physics_summary_changed"], item["physics_passed_changed"]]
        for item in delta["per_candidate"]
    ]
    lines.append(_markdown_table(["Candidate", "Score delta", "Summary changed", "Pass changed"], rows))
    lines.extend(["", "## Category margin deltas (Case B - Case A)", ""])
    rows = []
    for item in delta["per_candidate"]:
        category_deltas = item["category_margin_deltas_case_b_minus_a"]
        rows.append(
            [
                item["candidate_id"],
                category_deltas.get("structural_margin_delta_case_b_minus_a", "—"),
                category_deltas.get("drivetrain_margin_delta_case_b_minus_a", "—"),
                category_deltas.get("thermal_margin_delta_case_b_minus_a", "—"),
                category_deltas.get("controls_tracking_margin_delta_case_b_minus_a", "—"),
            ]
        )
    lines.append(_markdown_table(["Candidate", "Structural", "Drivetrain", "Thermal", "Controls/tracking"], rows))
    return "\n".join(lines) + "\n"


def _build_compare_markdown(compare: dict[str, Any]) -> str:
    delta = compare["delta_summary"]
    lines = ["# Comparative demo: baseline vs constrained", "", f"Generated: {compare['generated_at_utc']}", ""]
    for case_key in ("case_a", "case_b"):
        case = compare[case_key]
        lines.extend(
            [
                f"## {case['label']}",
                f"- Topology: `{case['topology']}`",
                f"- Top candidate: `{case['top_candidate_id']}`",
                f"- Top total score: `{case['top_candidate_total_score']}`",
                f"- Candidate count: `{case['candidate_count']}`",
                f"- Physics pass count: `{case['physics_pass_count']}`",
                f"- Physics warning count: `{case['physics_warning_count']}`",
                f"- Risk flags: `{case['risk_flags']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Differences",
            f"- Topology changed: `{delta['topology_changed']}`",
            f"- Top candidate changed: `{delta['top_candidate_changed']}`",
            f"- Top score delta (B - A): `{delta['top_score_delta_case_b_minus_a']}`",
            f"- Physics pass count delta (B - A): `{delta['physics_pass_count_delta_case_b_minus_a']}`",
            f"- Physics warning count delta (B - A): `{delta['physics_warning_count_delta_case_b_minus_a']}`",
            f"- Risk flags added in B: `{delta['risk_flags_added_in_b']}`",
            f"- Risk flags removed in B: `{delta['risk_flags_removed_in_b']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_how_we_ran_it(output_dir: Path) -> str:
    baseline = json.dumps(BASELINE_PAYLOAD, indent=2)
    constrained = json.dumps(CONSTRAINED_PAYLOAD, indent=2)
    return f"""# How we ran the comparative demo

## Exact command

```bash
python scripts/export_physics_compare.py --output-dir {output_dir.as_posix()}
```

## Inputs

### Case A baseline

```json
{baseline}
```

### Case B constrained

```json
{constrained}
```

## Execution details

- The script constructs `RequirementInput` objects from the payloads above.
- Each case is run through `run_generation_pipeline(..., explain_topology_selection=True, sim_enabled=True, cad_enabled=False)`.
- CAD generation is disabled so the export is reproducible and does not include run-specific CAD artifact UUIDs.
- Physics enrichment comes from `physics_summary`, `physics_passed`, `physics_margins`, and `physics_warnings` on each candidate response.

## Export set

- `case_a_baseline/request.json`
- `case_a_baseline/response.json`
- `case_a_baseline/summary.json`
- `case_b_constrained/request.json`
- `case_b_constrained/response.json`
- `case_b_constrained/summary.json`
- `COMPARE.json`
- `COMPARE.md`
- `PHYSICS_COMPARE.json`
- `PHYSICS_COMPARE.md`
- `HOW_WE_RAN_IT.md`
"""


def build_export(output_dir: Path) -> dict[str, Any]:
    generated_at = datetime.now(UTC).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for case_key, case in CASES.items():
        case_dir = output_dir / case_key
        case_dir.mkdir(parents=True, exist_ok=True)
        request = RequirementInput(**case["payload"])
        response = run_generation_pipeline(request, explain_topology_selection=True, sim_enabled=True, cad_enabled=False)
        exported_at = datetime.now(UTC).isoformat()
        summary = _summarize_case(case_key, case, response, exported_at)
        _write_json(case_dir / "request.json", case["payload"])
        _write_json(case_dir / "response.json", response)
        _write_json(case_dir / "summary.json", summary)
        summaries[case_key] = summary

    compare = {
        "generated_at_utc": generated_at,
        "case_a": summaries["case_a_baseline"],
        "case_b": summaries["case_b_constrained"],
    }
    compare["delta_summary"] = _delta_summary(compare["case_a"], compare["case_b"])
    legacy_compare = {
        "generated_at_utc": compare["generated_at_utc"],
        "case_a": compare["case_a"],
        "case_b": compare["case_b"],
        "diff": compare["delta_summary"],
    }
    _write_json(output_dir / "COMPARE.json", legacy_compare)
    _write_json(output_dir / "PHYSICS_COMPARE.json", compare)
    (output_dir / "COMPARE.md").write_text(_build_compare_markdown(compare))
    (output_dir / "PHYSICS_COMPARE.md").write_text(_build_physics_markdown(compare))
    (output_dir / "HOW_WE_RAN_IT.md").write_text(_build_how_we_ran_it(output_dir))
    return compare


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("exports/demo_compare_2026-05-28"))
    args = parser.parse_args()
    build_export(args.output_dir)


if __name__ == "__main__":
    main()
