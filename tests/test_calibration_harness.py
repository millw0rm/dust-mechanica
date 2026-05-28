from packages.domain.scoring.calibration import run_calibration


def test_calibration_runs_and_writes_report():
    report = run_calibration()
    assert 0.0 <= report["pass_rate"] <= 1.0
    assert "ranking_stability" in report
