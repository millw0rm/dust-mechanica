import json

from packages.domain.scoring.recalibrate import recalibrate_policy


def test_recalibration_is_deterministic_on_fixture(tmp_path):
    out_dir = tmp_path / "proposals"
    proposal = recalibrate_policy(
        feedback_path="tests/fixtures/recalibration/feedback.json",
        benchmark_path="tests/fixtures/recalibration/benchmarks.json",
        output_dir=str(out_dir),
        min_sample_size=4,
    )

    assert proposal["meta"]["decision"] == "candidate_generated"
    candidate = proposal["candidate_policy"]
    assert candidate["risk_thresholds"]["speed_headroom_factor"] == 1.075
    assert candidate["risk_thresholds"]["min_efficiency"] == 0.8595
    assert candidate["weight_perturbation"]["bound"] == 0.08
    assert candidate["weight_perturbation"]["samples"] == 25

    persisted = json.loads((out_dir / "latest.json").read_text())
    assert persisted["meta"]["sample_size"] == 4


def test_recalibration_noop_below_min_sample_size(tmp_path):
    out_dir = tmp_path / "proposals"
    proposal = recalibrate_policy(
        feedback_path="tests/fixtures/recalibration/feedback.json",
        benchmark_path="tests/fixtures/recalibration/benchmarks.json",
        output_dir=str(out_dir),
        min_sample_size=10,
    )

    assert proposal["meta"]["decision"] == "no_op_insufficient_sample"
    assert proposal["candidate_policy"] is None
    assert proposal["review_gate"]["approved"] is False
