from __future__ import annotations

import uuid


class JobRunner:
    def __init__(self, store, run_recorder) -> None:
        self.store = store
        self.run_recorder = run_recorder

    async def run_job(self, job: dict[str, object]) -> dict[str, object]:
        run_id = self.run_recorder.start_run("job", {"job_id": job["job_id"], "job_type": job["job_type"]})
        job_run = self.store.create_job_run(
            job_id=str(job["job_id"]),
            run_id=run_id,
            status="succeeded",
            attempt=1,
            backoff_seconds=0,
        )
        self.run_recorder.add_artifact(
            run_id=run_id,
            kind="job_run",
            payload={"job_run_id": job_run["job_run_id"], "job_id": job["job_id"], "result": "ok"},
        )
        self.run_recorder.finish_run(run_id=run_id, status="succeeded")
        return {
            "job_run_id": job_run["job_run_id"],
            "run_id": run_id,
            "status": "succeeded",
            "event_id": str(uuid.uuid4()),
        }
