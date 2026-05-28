
import json
from pathlib import Path


def _load(path):
    return json.loads(path.read_text()) if path.exists() else []


def load_catalog() -> dict:
    base = Path(__file__).parent / "data"
    return {
        "motors": _load(base / "motors.json"),
        "drives": _load(base / "drives.json"),
        "transmissions": _load(base / "transmissions.json"),
        "screws": _load(base / "screws.json"),
        "bearings": _load(base / "bearings.json"),
        "couplings": _load(base / "couplings.json"),
        "encoders": _load(base / "encoders.json"),
        "direct_drive_motors": _load(base / "direct_drive_motors.json"),
    }
