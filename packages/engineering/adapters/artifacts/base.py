from __future__ import annotations

from typing import Any, Protocol


class ArtifactStore(Protocol):
    """Persistence boundary for deterministic engineering artifacts."""

    def put_json(self, namespace: str, fingerprint: str, tool: str, name: str, payload: Any) -> str:
        """Persist a JSON-serializable payload and return its artifact URI."""
        ...

    def put_bytes(self, namespace: str, fingerprint: str, tool: str, name: str, payload: bytes) -> str:
        """Persist raw bytes and return their artifact URI."""
        ...

    def get(self, uri: str) -> bytes:
        """Return the bytes stored at an artifact URI."""
        ...
