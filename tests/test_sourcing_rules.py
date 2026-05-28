from packages.catalog.rules import evaluate_sourcing_rules


def test_eol_disallowed_and_single_source_flagged():
    r = evaluate_sourcing_rules({"lifecycle_state": "EOL", "single_source": True, "lead_time_days": 60}, allow_eol=False)
    assert r["disallowed"] is True
    assert "SINGLE_SOURCE_RISK" in r["flags"]
