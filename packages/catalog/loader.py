import json
from pathlib import Path


def load_catalog() -> dict:
    base = Path(__file__).parent / "data"
    return {
        "motors": json.loads((base / "motors.json").read_text()),
        "drives": json.loads((base / "drives.json").read_text()),
        "transmissions": json.loads((base / "transmissions.json").read_text()),
    }
