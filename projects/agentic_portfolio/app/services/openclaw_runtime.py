from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


ALLOWED_CAPABILITIES = {"update_job", "notification_channel"}


class OpenClawManifest(BaseModel):
    id: str
    version: str
    entrypoint: str
    capabilities: List[str]
    permissions: List[str] = Field(default_factory=list)


@dataclass
class PluginRecord:
    manifest: Optional[OpenClawManifest]
    status: str
    error: str | None
    source: str


class OpenClawRuntimeHost:
    def __init__(self, plugins_dir: Path, enabled: bool = True, timeout_seconds: float = 3.0) -> None:
        self.plugins_dir = plugins_dir
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self._plugins: Dict[str, PluginRecord] = {}

    def reload(self) -> Dict[str, object]:
        self._plugins = {}
        if not self.enabled:
            return {"enabled": False, "loaded": 0, "invalid": 0}
        if not self.plugins_dir.exists():
            return {"enabled": True, "loaded": 0, "invalid": 0}

        loaded = 0
        invalid = 0
        for manifest_path in sorted(self.plugins_dir.glob("*.json")):
            source = str(manifest_path)
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest = OpenClawManifest.model_validate(data)
                unsupported = sorted(set(manifest.capabilities) - ALLOWED_CAPABILITIES)
                if unsupported:
                    raise ValueError(f"Unsupported capabilities: {', '.join(unsupported)}")
                self._plugins[manifest.id] = PluginRecord(
                    manifest=manifest,
                    status="loaded",
                    error=None,
                    source=source,
                )
                loaded += 1
            except Exception as exc:
                plugin_key = manifest_path.stem
                self._plugins[plugin_key] = PluginRecord(
                    manifest=None,
                    status="invalid",
                    error=str(exc),
                    source=source,
                )
                invalid += 1
        return {"enabled": True, "loaded": loaded, "invalid": invalid}

    def status(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for plugin_id, record in sorted(self._plugins.items()):
            rows.append(
                {
                    "plugin_id": plugin_id,
                    "status": record.status,
                    "entrypoint": record.manifest.entrypoint if record.manifest else None,
                    "capabilities": record.manifest.capabilities if record.manifest else [],
                    "error": record.error,
                    "source": record.source,
                }
            )
        return rows

    def capabilities(self) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {key: [] for key in sorted(ALLOWED_CAPABILITIES)}
        for plugin_id, record in self._plugins.items():
            if record.status != "loaded" or record.manifest is None:
                continue
            for capability in record.manifest.capabilities:
                mapping.setdefault(capability, []).append(plugin_id)
        for key in mapping:
            mapping[key] = sorted(mapping[key])
        return mapping

    def invoke(self, plugin_id: str, capability: str, payload: Dict[str, object], run_id: str | None = None) -> Dict[str, object]:
        if not self.enabled:
            raise ValueError("OpenClaw runtime is disabled")
        record = self._plugins.get(plugin_id)
        if record is None or record.status != "loaded" or record.manifest is None:
            raise ValueError("Plugin is not loaded")
        if capability not in ALLOWED_CAPABILITIES:
            raise ValueError("Capability is not permitted")
        if capability not in record.manifest.capabilities:
            raise ValueError("Plugin does not declare this capability")

        started = time.perf_counter()
        correlation_id = str(uuid.uuid4())
        try:
            result = self._invoke_entrypoint(record.manifest.entrypoint, payload)
            elapsed_ms = (time.perf_counter() - started) * 1000
            if elapsed_ms > self.timeout_seconds * 1000:
                raise TimeoutError("Plugin invocation timed out")
            return {
                "ok": True,
                "plugin_id": plugin_id,
                "capability": capability,
                "correlation_id": correlation_id,
                "run_id": run_id,
                "elapsed_ms": elapsed_ms,
                "result": result,
            }
        except Exception as exc:
            return {
                "ok": False,
                "plugin_id": plugin_id,
                "capability": capability,
                "correlation_id": correlation_id,
                "run_id": run_id,
                "elapsed_ms": (time.perf_counter() - started) * 1000,
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }

    @staticmethod
    def _invoke_entrypoint(entrypoint: str, payload: Dict[str, object]) -> Dict[str, object]:
        if entrypoint == "builtin.echo":
            return {"payload": payload}
        if entrypoint == "builtin.timestamp":
            return {"payload": payload, "ts": time.time()}
        raise NotImplementedError(f"Entrypoint not implemented: {entrypoint}")
