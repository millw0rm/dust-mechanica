from packages.engineering.exceptions import UnitConversionError

UNIT_ALIASES = {
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "millimetre": "mm",
    "millimetres": "mm",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "m/s": "m/s",
    "mps": "m/s",
    "meter/s": "m/s",
    "meters/s": "m/s",
    "metre/s": "m/s",
    "metres/s": "m/s",
    "mm/s": "mm/s",
    "mmps": "mm/s",
    "millimeter/s": "mm/s",
    "millimeters/s": "mm/s",
    "millimetre/s": "mm/s",
    "millimetres/s": "mm/s",
}

CONVERSIONS = {
    ("m", "m"): 1.0,
    ("mm", "mm"): 1.0,
    ("mm", "m"): 0.001,
    ("m", "mm"): 1000.0,
    ("kg", "kg"): 1.0,
    ("g", "kg"): 0.001,
    ("kg", "g"): 1000.0,
    ("g", "g"): 1.0,
    ("mm/s", "m/s"): 0.001,
    ("m/s", "mm/s"): 1000.0,
    ("m/s", "m/s"): 1.0,
    ("mm/s", "mm/s"): 1.0,
}


def canonical_unit(unit: str) -> str:
    normalized = str(unit).strip().lower().replace(" ", "")
    return UNIT_ALIASES.get(normalized, normalized)


def normalize_quantity(value: float, unit: str, target_unit: str) -> float:
    source = canonical_unit(unit)
    target = canonical_unit(target_unit)
    key = (source, target)
    if key not in CONVERSIONS:
        raise UnitConversionError(f"Cannot convert {unit} to {target_unit}")
    return float(value) * CONVERSIONS[key]
