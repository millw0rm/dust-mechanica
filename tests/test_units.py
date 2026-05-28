from packages.engineering.units import normalize_quantity


def test_mm_to_m():
    assert normalize_quantity(1000, "mm", "m") == 1.0
