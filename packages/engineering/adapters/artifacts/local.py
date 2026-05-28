from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


@dataclass(frozen=True)
class LocalArtifactStore:
    """Filesystem-backed artifact store using stable `artifact://...` URIs."""

    root: Path | str = Path("artifacts")

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))

    def put_json(self, namespace: str, fingerprint: str, tool: str, name: str, payload: Any) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str, indent=2).encode("utf-8") + b"\n"
        return self.put_bytes(namespace, fingerprint, tool, name, encoded)

    def put_bytes(self, namespace: str, fingerprint: str, tool: str, name: str, payload: bytes) -> str:
        path = self.path_for(namespace, fingerprint, tool, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return self.uri_for(namespace, fingerprint, tool, name)

    def get(self, uri: str) -> bytes:
        return self.path_for_uri(uri).read_bytes()

    def uri_for(self, namespace: str, fingerprint: str, tool: str, name: str) -> str:
        namespace, fingerprint, tool, name = self._validated_parts(namespace, fingerprint, tool, name)
        return f"artifact://{namespace}/{fingerprint}/{tool}/{name}"

    def path_for(self, namespace: str, fingerprint: str, tool: str, name: str) -> Path:
        namespace, fingerprint, tool, name = self._validated_parts(namespace, fingerprint, tool, name)
        return self.root / namespace / fingerprint / tool / name

    def path_for_uri(self, uri: str) -> Path:
        parsed = urlparse(uri)
        if parsed.scheme != "artifact" or not parsed.netloc:
            raise ValueError(f"Unsupported artifact URI: {uri}")
        parts = [unquote(part) for part in parsed.path.split("/") if part]
        if len(parts) != 3:
            raise ValueError(f"Artifact URI must be artifact://<namespace>/<fingerprint>/<tool>/<name>: {uri}")
        namespace = unquote(parsed.netloc)
        fingerprint, tool, name = parts
        return self.path_for(namespace, fingerprint, tool, name)

    def _validated_parts(self, namespace: str, fingerprint: str, tool: str, name: str) -> tuple[str, str, str, str]:
        return (
            self._validate_segment("namespace", namespace),
            self._validate_segment("fingerprint", fingerprint),
            self._validate_segment("tool", tool),
            self._validate_segment("name", name),
        )

    def _validate_segment(self, label: str, value: str) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"Artifact {label} must be a non-empty string")
        if value in {".", ".."} or "/" in value or "\\" in value:
            raise ValueError(f"Artifact {label} must be a single path segment: {value}")
        return value
