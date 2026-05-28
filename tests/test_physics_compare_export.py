import json

from scripts.export_physics_compare import build_export


def test_physics_compare_export_includes_margins_tables_and_deltas(tmp_path):
    out_dir = tmp_path / "demo_compare"
    compare = build_export(out_dir)

    physics_json = json.loads((out_dir / "PHYSICS_COMPARE.json").read_text())
    assert physics_json["case_a"]["per_candidate_physics_margins"]
    assert physics_json["case_b"]["per_candidate_physics_margins"]
    assert set(physics_json["case_a"]["pass_fail_by_check_type"]) == {
        "structural",
        "thermal",
        "drivetrain",
        "controls",
    }
    assert "per_candidate" in physics_json["delta_summary"]
    assert physics_json["delta_summary"]["safest_candidate_case_a"]
    assert physics_json["delta_summary"]["safest_candidate_case_b"]
    category_deltas = physics_json["delta_summary"]["per_candidate"][0]["category_margin_deltas_case_b_minus_a"]
    assert set(category_deltas) == {
        "structural_margin_delta_case_b_minus_a",
        "drivetrain_margin_delta_case_b_minus_a",
        "thermal_margin_delta_case_b_minus_a",
        "controls_tracking_margin_delta_case_b_minus_a",
    }
    assert compare["delta_summary"] == physics_json["delta_summary"]

    physics_md = (out_dir / "PHYSICS_COMPARE.md").read_text()
    for section in ("## structural", "## thermal", "## drivetrain", "## controls"):
        assert section in physics_md
    assert "## Delta summary across cases" in physics_md
    assert "## Safest candidate summary" in physics_md
    assert "## Category margin deltas (Case B - Case A)" in physics_md
    assert "Controls/tracking" in physics_md
    assert "speed_headroom_ratio" in physics_md

    how_we_ran_it = (out_dir / "HOW_WE_RAN_IT.md").read_text()
    assert "python scripts/export_physics_compare.py --output-dir" in how_we_ran_it
    assert "run_generation_pipeline" in how_we_ran_it
