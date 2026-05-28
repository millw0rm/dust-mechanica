from packages.engineering.exceptions import UnitConversionError

CONVERSIONS = {
    ("mm", "m"): 0.001,
    ("m", "mm"): 1000.0,
    ("kg", "kg"): 1.0,
    ("g", "kg"): 0.001,
    ("kg", "g"): 1000.0,
    ("mm/s", "m/s"): 0.001,
    ("m/s", "mm/s"): 1000.0,
}


def normalize_quantity(value: float, unit: str, target_unit: str) -> float:
    key = (unit, target_unit)
    if key not in CONVERSIONS:
        raise UnitConversionError(f"Cannot convert {unit} to {target_unit}")
    return value * CONVERSIONS[key]
