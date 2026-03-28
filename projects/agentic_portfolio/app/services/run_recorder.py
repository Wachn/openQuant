from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunRecorder:
    def __init__(self, store) -> None:
        self.store = store

    def start_run(self, run_type: str, config: dict[str, object]) -> str:
        run_id = str(uuid.uuid4())
        config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()
        self.store.create_run(run_id=run_id, run_type=run_type, config_hash=config_hash, metadata={"v": "2.1"})
        return run_id

    def finish_run(self, run_id: str, status: str) -> None:
        normalized = "finished" if status == "succeeded" else "failed" if status == "failed" else status
        self.store.finish_run(run_id=run_id, state=normalized)

    def add_artifact(self, run_id: str, kind: str, payload: dict[str, object]) -> str:
        artifact_id = str(uuid.uuid4())
        self.store.add_artifact(artifact_id=artifact_id, run_id=run_id, artifact_type=kind, payload=payload)
        return artifact_id
