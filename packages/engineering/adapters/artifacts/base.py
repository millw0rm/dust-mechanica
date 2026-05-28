from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ArtifactStore(Protocol):
    """Persistence contract for deterministic toolchain artifacts."""

    def put_json(self, namespace: str, fingerprint: str, tool: str, name: str, payload: Any) -> str:
        """Persist a JSON-serializable payload and return its artifact URI."""
        ...

    def put_bytes(self, namespace: str, fingerprint: str, tool: str, name: str, payload: bytes) -> str:
        """Persist raw bytes and return their artifact URI."""
        ...

    def get(self, uri: str) -> bytes:
        """Return the raw bytes stored at an artifact URI."""
        ...
