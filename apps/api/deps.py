from uuid import uuid4


def get_trace_id() -> str:
    return str(uuid4())
