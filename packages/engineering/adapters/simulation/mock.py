class MockSimulationAdapter:
    def run(self, model_input: dict) -> dict:
        return {"status":"ok","echo":model_input}
