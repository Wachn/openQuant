from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class V21Store:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS v21_provider_profiles (
                    provider_profile_id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    auth_type TEXT NOT NULL,
                    base_url TEXT,
                    options_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_health_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS v21_model_profiles (
                    model_profile_id TEXT PRIMARY KEY,
                    provider_profile_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    default_temperature REAL,
                    max_output_tokens INTEGER,
                    enabled INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(provider_profile_id) REFERENCES v21_provider_profiles(provider_profile_id)
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_v21_model_profiles_unique
                ON v21_model_profiles(provider_profile_id, model_id)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS v21_findings (
                    finding_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    severity TEXT NOT NULL,
                    finding_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    evidence_artifact_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS v21_reports (
                    report_id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL,
                    account_id TEXT,
                    title TEXT NOT NULL,
                    body_md TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    run_id TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS v21_jobs (
                    job_id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    schedule_cron TEXT,
                    enabled INTEGER NOT NULL,
                    config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS v21_job_runs (
                    job_run_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    run_id TEXT,
                    status TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    backoff_seconds INTEGER NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES v21_jobs(job_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS v21_notifications (
                    notification_id TEXT PRIMARY KEY,
                    channel TEXT NOT NULL,
                    to_address TEXT NOT NULL,
                    subject TEXT,
                    body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS v21_broker_orders (
                    order_id TEXT PRIMARY KEY,
                    broker_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    client_order_id TEXT,
                    idempotency_key TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def list_provider_profiles(self) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT provider_profile_id, provider_id, display_name, auth_type, base_url, options_json, status,
                       last_health_at, created_at, updated_at
                FROM v21_provider_profiles
                ORDER BY created_at
                """
            ).fetchall()
        return [
            {
                "provider_profile_id": row[0],
                "provider_id": row[1],
                "display_name": row[2],
                "auth_type": row[3],
                "base_url": row[4],
                "options": json.loads(row[5]),
                "status": row[6],
                "last_health_at": row[7],
                "created_at": row[8],
                "updated_at": row[9],
            }
            for row in rows
        ]

    def upsert_provider_profile(
        self,
        provider_profile_id: str,
        provider_id: str,
        display_name: str,
        auth_type: str,
        base_url: str | None,
        options: dict[str, object],
        status: str,
        last_health_at: str | None,
    ) -> dict[str, object]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO v21_provider_profiles(
                    provider_profile_id, provider_id, display_name, auth_type, base_url, options_json, status,
                    last_health_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_profile_id) DO UPDATE SET
                    provider_id = excluded.provider_id,
                    display_name = excluded.display_name,
                    auth_type = excluded.auth_type,
                    base_url = excluded.base_url,
                    options_json = excluded.options_json,
                    status = excluded.status,
                    last_health_at = excluded.last_health_at,
                    updated_at = excluded.updated_at
                """,
                (
                    provider_profile_id,
                    provider_id,
                    display_name,
                    auth_type,
                    base_url,
                    json.dumps(options),
                    status,
                    last_health_at,
                    now,
                    now,
                ),
            )
        profile = next((item for item in self.list_provider_profiles() if item["provider_profile_id"] == provider_profile_id), None)
        if profile is None:
            raise ValueError("provider profile upsert failed")
        return profile

    def list_model_profiles(self) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT model_profile_id, provider_profile_id, model_id, display_name, capabilities_json,
                       default_temperature, max_output_tokens, enabled, created_at, updated_at
                FROM v21_model_profiles
                ORDER BY created_at
                """
            ).fetchall()
        return [
            {
                "model_profile_id": row[0],
                "provider_profile_id": row[1],
                "model_id": row[2],
                "display_name": row[3],
                "capabilities": json.loads(row[4]),
                "default_temperature": row[5],
                "max_output_tokens": row[6],
                "enabled": bool(row[7]),
                "created_at": row[8],
                "updated_at": row[9],
            }
            for row in rows
        ]

    def upsert_model_profile(
        self,
        model_profile_id: str,
        provider_profile_id: str,
        model_id: str,
        display_name: str,
        capabilities: dict[str, object],
        default_temperature: float | None,
        max_output_tokens: int | None,
        enabled: bool,
    ) -> dict[str, object]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO v21_model_profiles(
                    model_profile_id, provider_profile_id, model_id, display_name, capabilities_json,
                    default_temperature, max_output_tokens, enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_profile_id) DO UPDATE SET
                    provider_profile_id = excluded.provider_profile_id,
                    model_id = excluded.model_id,
                    display_name = excluded.display_name,
                    capabilities_json = excluded.capabilities_json,
                    default_temperature = excluded.default_temperature,
                    max_output_tokens = excluded.max_output_tokens,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (
                    model_profile_id,
                    provider_profile_id,
                    model_id,
                    display_name,
                    json.dumps(capabilities),
                    default_temperature,
                    max_output_tokens,
                    1 if enabled else 0,
                    now,
                    now,
                ),
            )
        model = next((item for item in self.list_model_profiles() if item["model_profile_id"] == model_profile_id), None)
        if model is None:
            raise ValueError("model profile upsert failed")
        return model

    def list_findings(self, session_id: str | None = None, status: str | None = None) -> list[dict[str, object]]:
        query = (
            "SELECT finding_id, session_id, severity, finding_type, title, summary, status, evidence_artifact_id, created_at, updated_at "
            "FROM v21_findings"
        )
        clauses: list[str] = []
        params: list[object] = []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {
                "finding_id": row[0],
                "session_id": row[1],
                "severity": row[2],
                "finding_type": row[3],
                "title": row[4],
                "summary": row[5],
                "status": row[6],
                "evidence_artifact_id": row[7],
                "created_at": row[8],
                "updated_at": row[9],
            }
            for row in rows
        ]

    def create_finding(
        self,
        severity: str,
        finding_type: str,
        title: str,
        summary: str,
        session_id: str | None = None,
        evidence_artifact_id: str | None = None,
    ) -> dict[str, object]:
        now = utc_now_iso()
        finding_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO v21_findings(
                    finding_id, session_id, severity, finding_type, title, summary, status, evidence_artifact_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
                """,
                (finding_id, session_id, severity, finding_type, title, summary, evidence_artifact_id, now, now),
            )
        return self.list_findings()[0]

    def resolve_finding(self, finding_id: str) -> bool:
        now = utc_now_iso()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE v21_findings SET status = 'resolved', updated_at = ? WHERE finding_id = ?",
                (now, finding_id),
            )
        return cur.rowcount > 0

    def list_reports(self, report_type: str | None = None, account_id: str | None = None) -> list[dict[str, object]]:
        query = "SELECT report_id, report_type, account_id, title, body_md, summary_json, run_id, created_at FROM v21_reports"
        clauses: list[str] = []
        params: list[object] = []
        if report_type:
            clauses.append("report_type = ?")
            params.append(report_type)
        if account_id:
            clauses.append("account_id = ?")
            params.append(account_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {
                "report_id": row[0],
                "report_type": row[1],
                "account_id": row[2],
                "title": row[3],
                "body_md": row[4],
                "summary": json.loads(row[5]),
                "run_id": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]

    def create_report(
        self,
        report_type: str,
        title: str,
        body_md: str,
        summary: dict[str, object],
        account_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, object]:
        report_id = str(uuid.uuid4())
        created_at = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO v21_reports(report_id, report_type, account_id, title, body_md, summary_json, run_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (report_id, report_type, account_id, title, body_md, json.dumps(summary), run_id, created_at),
            )
        reports = self.list_reports()
        created = next((item for item in reports if item["report_id"] == report_id), None)
        if created is None:
            raise ValueError("report create failed")
        return created

    def list_jobs(self) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT job_id, job_type, name, schedule_cron, enabled, config_json, created_at, updated_at
                FROM v21_jobs
                ORDER BY created_at
                """
            ).fetchall()
        return [
            {
                "job_id": row[0],
                "job_type": row[1],
                "name": row[2],
                "schedule_cron": row[3],
                "enabled": bool(row[4]),
                "config": json.loads(row[5]),
                "created_at": row[6],
                "updated_at": row[7],
            }
            for row in rows
        ]

    def upsert_job(
        self,
        job_id: str,
        job_type: str,
        name: str,
        schedule_cron: str | None,
        enabled: bool,
        config: dict[str, object],
    ) -> dict[str, object]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO v21_jobs(job_id, job_type, name, schedule_cron, enabled, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    job_type = excluded.job_type,
                    name = excluded.name,
                    schedule_cron = excluded.schedule_cron,
                    enabled = excluded.enabled,
                    config_json = excluded.config_json,
                    updated_at = excluded.updated_at
                """,
                (job_id, job_type, name, schedule_cron, 1 if enabled else 0, json.dumps(config), now, now),
            )
        job = next((item for item in self.list_jobs() if item["job_id"] == job_id), None)
        if job is None:
            raise ValueError("job upsert failed")
        return job

    def create_job_run(
        self,
        job_id: str,
        run_id: str,
        status: str,
        attempt: int = 1,
        backoff_seconds: int = 0,
        error: str | None = None,
    ) -> dict[str, object]:
        job_run_id = str(uuid.uuid4())
        now = utc_now_iso()
        finished_at = now if status in {"succeeded", "failed", "canceled"} else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO v21_job_runs(
                    job_run_id, job_id, run_id, status, attempt, backoff_seconds, started_at, finished_at, error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (job_run_id, job_id, run_id, status, attempt, backoff_seconds, now, finished_at, error, now),
            )
        return {
            "job_run_id": job_run_id,
            "job_id": job_id,
            "run_id": run_id,
            "status": status,
            "attempt": attempt,
            "backoff_seconds": backoff_seconds,
            "started_at": now,
            "finished_at": finished_at,
            "error": error,
            "created_at": now,
        }

    def list_job_runs(self, job_id: str | None = None) -> list[dict[str, object]]:
        query = (
            "SELECT job_run_id, job_id, run_id, status, attempt, backoff_seconds, started_at, finished_at, error, created_at "
            "FROM v21_job_runs"
        )
        params: tuple[object, ...] = tuple()
        if job_id:
            query += " WHERE job_id = ?"
            params = (job_id,)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "job_run_id": row[0],
                "job_id": row[1],
                "run_id": row[2],
                "status": row[3],
                "attempt": row[4],
                "backoff_seconds": row[5],
                "started_at": row[6],
                "finished_at": row[7],
                "error": row[8],
                "created_at": row[9],
            }
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
