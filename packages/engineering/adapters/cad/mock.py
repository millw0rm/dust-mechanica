class MockCADAdapter:
    def build(self, model_input: dict) -> dict:
        return {"status":"ok","echo":model_input}
