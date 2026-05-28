from typing import Protocol

class SimulationAdapter(Protocol):
    def run(self, model_input: dict) -> dict: ...
