from typing import Protocol

class CADAdapter(Protocol):
    def build(self, model_input: dict) -> dict: ...
