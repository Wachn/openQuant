from __future__ import annotations

import sqlite3
import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    as_of_ts TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    as_of_ts TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    raw_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    run_type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    config_hash TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS suggestions (
                    suggestion_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_orders (
                    idempotency_key TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    ticket_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_execution_orders_order_id
                ON execution_orders(order_id)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_events (
                    event_id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    state TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    route TEXT,
                    artifact_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS change_requests (
                    change_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    snooze_until TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_connections (
                    connection_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    base_url TEXT,
                    api_key_env TEXT,
                    enabled INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_provider_bindings (
                    agent_id TEXT PRIMARY KEY,
                    connection_id TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_route_traces (
                    trace_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    route TEXT NOT NULL,
                    connector_id TEXT,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_memory_summaries (
                    summary_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    message_count INTEGER NOT NULL,
                    token_estimate INTEGER NOT NULL,
                    summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS news_cache (
                    news_id TEXT PRIMARY KEY,
                    dedupe_key TEXT NOT NULL,
                    source TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    news_category TEXT,
                    news_class TEXT,
                    published_at TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_news_cache_dedupe_key
                ON news_cache(dedupe_key)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_cache_published_at
                ON news_cache(published_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_cache_expires_at
                ON news_cache(expires_at)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_cache_filters
                ON news_cache(source, news_category, news_class, published_at DESC)
                """
            )
            conn.execute(
                """
                INSERT INTO meta(key, value, updated_at)
                VALUES ('initialized_at', ?, ?)
                ON CONFLICT(key) DO NOTHING
                """,
                (utc_now_iso(), utc_now_iso()),
            )

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO app_settings(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, utc_now_iso()),
            )

    def get_settings(self) -> Dict[str, str]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT key, value FROM app_settings ORDER BY key")
            rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    def get_meta(self) -> Dict[str, str]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT key, value FROM meta ORDER BY key")
            rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    def upsert_portfolio_snapshot(self, as_of_ts: str, payload: Dict[str, object]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO portfolio_snapshots(as_of_ts, payload_json, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(as_of_ts) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    created_at = excluded.created_at
                """,
                (as_of_ts, json.dumps(payload), utc_now_iso()),
            )

    def latest_portfolio_snapshot(self) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT payload_json FROM portfolio_snapshots ORDER BY as_of_ts DESC LIMIT 1"
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def upsert_market_snapshot(
        self,
        snapshot_id: str,
        as_of_ts: str,
        symbol: str,
        asset: str,
        payload: Dict[str, object],
        raw_hash: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO market_snapshots(snapshot_id, as_of_ts, symbol, asset, payload_json, raw_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id) DO UPDATE SET
                    as_of_ts = excluded.as_of_ts,
                    payload_json = excluded.payload_json,
                    raw_hash = excluded.raw_hash,
                    created_at = excluded.created_at
                """,
                (snapshot_id, as_of_ts, symbol, asset, json.dumps(payload), raw_hash, utc_now_iso()),
            )

    def latest_market_snapshots(self) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT m.payload_json FROM market_snapshots m
                INNER JOIN (
                    SELECT symbol, MAX(as_of_ts) AS max_ts
                    FROM market_snapshots
                    GROUP BY symbol
                ) latest
                  ON m.symbol = latest.symbol AND m.as_of_ts = latest.max_ts
                ORDER BY m.symbol
                """
            )
            rows = cursor.fetchall()
        return [json.loads(row[0]) for row in rows]

    def market_snapshot_diff(self) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                WITH ranked AS (
                    SELECT symbol, payload_json, as_of_ts,
                           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY as_of_ts DESC) AS rn
                    FROM market_snapshots
                )
                SELECT r1.symbol, r1.payload_json AS current_payload, r2.payload_json AS previous_payload
                FROM ranked r1
                LEFT JOIN ranked r2 ON r1.symbol = r2.symbol AND r2.rn = 2
                WHERE r1.rn = 1
                ORDER BY r1.symbol
                """
            )
            rows = cursor.fetchall()

        diff_rows: List[Dict[str, object]] = []
        for row in rows:
            current = json.loads(row[1])
            previous = json.loads(row[2]) if row[2] else None
            previous_change = float(previous.get("change_pct", 0.0)) if previous else 0.0
            current_change = float(current.get("change_pct", 0.0))
            diff_rows.append(
                {
                    "symbol": row[0],
                    "current": current,
                    "previous": previous,
                    "delta_change_pct": current_change - previous_change,
                }
            )
        return diff_rows

    def create_run(self, run_id: str, run_type: str, config_hash: str, metadata: Dict[str, str]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs(run_id, run_type, state, started_at, finished_at, config_hash, metadata_json)
                VALUES (?, ?, 'running', ?, NULL, ?, ?)
                """,
                (run_id, run_type, utc_now_iso(), config_hash, json.dumps(metadata)),
            )

    def finish_run(self, run_id: str, state: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE runs
                SET state = ?, finished_at = ?
                WHERE run_id = ?
                """,
                (state, utc_now_iso(), run_id),
            )

    def get_run(self, run_id: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT run_id, run_type, state, started_at, finished_at, config_hash, metadata_json
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "run_id": row[0],
            "run_type": row[1],
            "state": row[2],
            "started_at": row[3],
            "finished_at": row[4],
            "config_hash": row[5],
            "metadata": json.loads(row[6]),
        }

    def add_artifact(self, artifact_id: str, run_id: str, artifact_type: str, payload: Dict[str, object]) -> None:
        payload_json = json.dumps(payload)
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO artifacts(artifact_id, run_id, artifact_type, payload_json, payload_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (artifact_id, run_id, artifact_type, payload_json, payload_hash, utc_now_iso()),
            )

    def artifacts_for_run(self, run_id: str) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT artifact_id, artifact_type, payload_json, payload_hash, created_at
                FROM artifacts
                WHERE run_id = ?
                ORDER BY created_at
                """,
                (run_id,),
            )
            rows = cursor.fetchall()
        return [
            {
                "artifact_id": row[0],
                "artifact_type": row[1],
                "payload": json.loads(row[2]),
                "payload_hash": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]

    def upsert_suggestion(self, suggestion_id: str, status: str, payload: Dict[str, object]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO suggestions(suggestion_id, status, payload_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(suggestion_id) DO UPDATE SET
                    status = excluded.status,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (suggestion_id, status, json.dumps(payload), utc_now_iso()),
            )

    def list_suggestions(self, status: Optional[str] = None) -> List[Dict[str, object]]:
        query = "SELECT suggestion_id, status, payload_json, updated_at FROM suggestions"
        params: Tuple[object, ...] = tuple()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY updated_at DESC"

        with self._connect() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        return [
            {
                "suggestion_id": row[0],
                "status": row[1],
                "payload": json.loads(row[2]),
                "updated_at": row[3],
            }
            for row in rows
        ]

    def upsert_execution_order(
        self,
        idempotency_key: str,
        order_id: str,
        ticket_id: str,
        run_id: str,
        status: str,
        payload: Dict[str, object],
    ) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO execution_orders(idempotency_key, order_id, ticket_id, run_id, status, payload_json, submitted_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    status = excluded.status,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (idempotency_key, order_id, ticket_id, run_id, status, json.dumps(payload), now, now),
            )

    def get_execution_order(self, idempotency_key: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT order_id, ticket_id, run_id, status, payload_json, submitted_at, updated_at
                FROM execution_orders
                WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "idempotency_key": idempotency_key,
            "order_id": row[0],
            "ticket_id": row[1],
            "run_id": row[2],
            "status": row[3],
            "payload": json.loads(row[4]),
            "submitted_at": row[5],
            "updated_at": row[6],
        }

    def get_execution_order_by_order_id(self, order_id: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT idempotency_key, order_id, ticket_id, run_id, status, payload_json, submitted_at, updated_at
                FROM execution_orders
                WHERE order_id = ?
                """,
                (order_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "idempotency_key": row[0],
            "order_id": row[1],
            "ticket_id": row[2],
            "run_id": row[3],
            "status": row[4],
            "payload": json.loads(row[5]),
            "submitted_at": row[6],
            "updated_at": row[7],
        }

    def list_execution_orders(self) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT idempotency_key, order_id, ticket_id, run_id, status, payload_json, submitted_at, updated_at
                FROM execution_orders
                ORDER BY submitted_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "idempotency_key": row[0],
                "order_id": row[1],
                "ticket_id": row[2],
                "run_id": row[3],
                "status": row[4],
                "payload": json.loads(row[5]),
                "submitted_at": row[6],
                "updated_at": row[7],
            }
            for row in rows
        ]

    def update_execution_order(self, order_id: str, status: str, payload: Dict[str, object]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE execution_orders
                SET status = ?, payload_json = ?, updated_at = ?
                WHERE order_id = ?
                """,
                (status, json.dumps(payload), utc_now_iso(), order_id),
            )

    def add_execution_event(
        self,
        event_id: str,
        order_id: str,
        run_id: str,
        event_type: str,
        payload: Dict[str, object],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO execution_events(event_id, order_id, run_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, order_id, run_id, event_type, json.dumps(payload), utc_now_iso()),
            )

    def execution_events_for_order(self, order_id: str) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT event_id, order_id, run_id, event_type, payload_json, created_at
                FROM execution_events
                WHERE order_id = ?
                ORDER BY created_at
                """,
                (order_id,),
            )
            rows = cursor.fetchall()
        return [
            {
                "event_id": row[0],
                "order_id": row[1],
                "run_id": row[2],
                "event_type": row[3],
                "payload": json.loads(row[4]),
                "created_at": row[5],
            }
            for row in rows
        ]

    def create_chat_session(self, session_id: str, title: str, metadata: Dict[str, object]) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions(session_id, title, state, metadata_json, created_at, updated_at)
                VALUES (?, ?, 'active', ?, ?, ?)
                """,
                (session_id, title, json.dumps(metadata), now, now),
            )

    def get_chat_session(self, session_id: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT session_id, title, state, metadata_json, created_at, updated_at
                FROM chat_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "session_id": row[0],
            "title": row[1],
            "state": row[2],
            "metadata": json.loads(row[3]),
            "created_at": row[4],
            "updated_at": row[5],
        }

    def list_chat_sessions(self) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT session_id, title, state, metadata_json, created_at, updated_at
                FROM chat_sessions
                ORDER BY updated_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "session_id": row[0],
                "title": row[1],
                "state": row[2],
                "metadata": json.loads(row[3]),
                "created_at": row[4],
                "updated_at": row[5],
            }
            for row in rows
        ]

    def rename_chat_session(self, session_id: str, title: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE chat_sessions
                SET title = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (title, utc_now_iso(), session_id),
            )
            return cursor.rowcount > 0

    def add_chat_message(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: str,
        route: str | None,
        artifact: Dict[str, object] | None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages(message_id, session_id, role, content, route, artifact_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    route,
                    json.dumps(artifact) if artifact is not None else None,
                    utc_now_iso(),
                ),
            )
            conn.execute(
                """
                UPDATE chat_sessions
                SET updated_at = ?
                WHERE session_id = ?
                """,
                (utc_now_iso(), session_id),
            )

    def list_chat_messages(self, session_id: str) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT message_id, role, content, route, artifact_json, created_at
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at
                """,
                (session_id,),
            )
            rows = cursor.fetchall()
        return [
            {
                "message_id": row[0],
                "role": row[1],
                "content": row[2],
                "route": row[3],
                "artifact": json.loads(row[4]) if row[4] else None,
                "created_at": row[5],
            }
            for row in rows
        ]

    def delete_chat_session(self, session_id: str) -> bool:
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM chat_messages
                WHERE session_id = ?
                """,
                (session_id,),
            )
            cursor = conn.execute(
                """
                DELETE FROM chat_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            )
            deleted = cursor.rowcount > 0
        return deleted

    def upsert_change_request(
        self,
        change_id: str,
        status: str,
        summary: str,
        payload: Dict[str, object],
        snooze_until: str | None,
    ) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO change_requests(change_id, status, summary, payload_json, snooze_until, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(change_id) DO UPDATE SET
                    status = excluded.status,
                    summary = excluded.summary,
                    payload_json = excluded.payload_json,
                    snooze_until = excluded.snooze_until,
                    updated_at = excluded.updated_at
                """,
                (change_id, status, summary, json.dumps(payload), snooze_until, now, now),
            )

    def list_change_requests(self, status: str | None = None) -> List[Dict[str, object]]:
        query = """
            SELECT change_id, status, summary, payload_json, snooze_until, created_at, updated_at
            FROM change_requests
        """
        params: Tuple[object, ...] = tuple()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY updated_at DESC"
        with self._connect() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        return [
            {
                "change_id": row[0],
                "status": row[1],
                "summary": row[2],
                "payload": json.loads(row[3]),
                "snooze_until": row[4],
                "created_at": row[5],
                "updated_at": row[6],
            }
            for row in rows
        ]

    def upsert_provider_connection(
        self,
        connection_id: str,
        provider: str,
        model: str,
        base_url: str | None,
        api_key_env: str | None,
        enabled: bool,
        metadata: Dict[str, object],
    ) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO provider_connections(connection_id, provider, model, base_url, api_key_env, enabled, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(connection_id) DO UPDATE SET
                    provider = excluded.provider,
                    model = excluded.model,
                    base_url = excluded.base_url,
                    api_key_env = excluded.api_key_env,
                    enabled = excluded.enabled,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    connection_id,
                    provider,
                    model,
                    base_url,
                    api_key_env,
                    1 if enabled else 0,
                    json.dumps(metadata),
                    now,
                    now,
                ),
            )

    def list_provider_connections(self) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT connection_id, provider, model, base_url, api_key_env, enabled, metadata_json, created_at, updated_at
                FROM provider_connections
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "connection_id": row[0],
                "provider": row[1],
                "model": row[2],
                "base_url": row[3],
                "api_key_env": row[4],
                "enabled": bool(row[5]),
                "metadata": json.loads(row[6]),
                "created_at": row[7],
                "updated_at": row[8],
            }
            for row in rows
        ]

    def get_provider_connection(self, connection_id: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT connection_id, provider, model, base_url, api_key_env, enabled, metadata_json, created_at, updated_at
                FROM provider_connections
                WHERE connection_id = ?
                """,
                (connection_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "connection_id": row[0],
            "provider": row[1],
            "model": row[2],
            "base_url": row[3],
            "api_key_env": row[4],
            "enabled": bool(row[5]),
            "metadata": json.loads(row[6]),
            "created_at": row[7],
            "updated_at": row[8],
        }

    def bind_agent_provider_connection(self, agent_id: str, connection_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_provider_bindings(agent_id, connection_id, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    connection_id = excluded.connection_id,
                    updated_at = excluded.updated_at
                """,
                (agent_id, connection_id, utc_now_iso()),
            )

    def get_agent_provider_binding(self, agent_id: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT agent_id, connection_id, updated_at
                FROM agent_provider_bindings
                WHERE agent_id = ?
                """,
                (agent_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "agent_id": row[0],
            "connection_id": row[1],
            "updated_at": row[2],
        }

    def add_runtime_route_trace(
        self,
        trace_id: str,
        session_id: str,
        route: str,
        connector_id: str | None,
        status: str,
        metadata: Dict[str, object],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_route_traces(trace_id, session_id, route, connector_id, status, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    session_id,
                    route,
                    connector_id,
                    status,
                    json.dumps(metadata),
                    utc_now_iso(),
                ),
            )

    def list_runtime_route_traces(self, session_id: str, limit: int = 20) -> List[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT trace_id, session_id, route, connector_id, status, metadata_json, created_at
                FROM runtime_route_traces
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (session_id, max(1, min(limit, 200))),
            )
            rows = cursor.fetchall()
        return [
            {
                "trace_id": row[0],
                "session_id": row[1],
                "route": row[2],
                "connector_id": row[3],
                "status": row[4],
                "metadata": json.loads(row[5]),
                "created_at": row[6],
            }
            for row in rows
        ]

    def add_runtime_memory_summary(
        self,
        summary_id: str,
        session_id: str,
        message_count: int,
        token_estimate: int,
        summary: Dict[str, object],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_memory_summaries(summary_id, session_id, message_count, token_estimate, summary_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    summary_id,
                    session_id,
                    message_count,
                    token_estimate,
                    json.dumps(summary),
                    utc_now_iso(),
                ),
            )

    def latest_runtime_memory_summary(self, session_id: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT summary_id, session_id, message_count, token_estimate, summary_json, created_at
                FROM runtime_memory_summaries
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (session_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "summary_id": row[0],
            "session_id": row[1],
            "message_count": row[2],
            "token_estimate": row[3],
            "summary": json.loads(row[4]),
            "created_at": row[5],
        }

    def upsert_news_cache_items(self, items: List[Dict[str, object]], ttl_days: int = 60) -> int:
        now = datetime.now(timezone.utc)
        fetched_at = now.isoformat()
        stored = 0
        with self._connect() as conn:
            for item in items:
                if not isinstance(item, dict):
                    continue
                source = str(item.get("source") or "").strip().lower()
                url = str(item.get("url") or "").strip()
                title = str(item.get("title") or "").strip()
                if not source or not url or not title:
                    continue
                symbol = str(item.get("symbol") or "-").strip().upper() or "-"
                summary = str(item.get("summary") or "").strip()
                thumbnail_url = str(item.get("thumbnail_url") or "").strip() or None
                news_category = str(item.get("news_category") or "").strip().lower() or None
                news_class = str(item.get("news_class") or "").strip().lower() or None
                published_at = str(item.get("published_at") or "").strip() or fetched_at
                try:
                    published_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    if published_dt.tzinfo is None:
                        published_dt = published_dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    published_dt = now
                    published_at = fetched_at
                expires_at = (published_dt + timedelta(days=max(1, ttl_days))).astimezone(timezone.utc).isoformat()
                base_key = f"{source}|{url}"
                dedupe_key = hashlib.sha256(base_key.encode("utf-8")).hexdigest()
                normalized_item = dict(item)
                news_id = f"{source}:{dedupe_key}"
                normalized_item["news_id"] = news_id
                payload_json = json.dumps(normalized_item)
                conn.execute(
                    """
                    INSERT INTO news_cache(
                        news_id, dedupe_key, source, symbol, title, summary, url, thumbnail_url,
                        news_category, news_class, published_at, fetched_at, expires_at, payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(dedupe_key) DO UPDATE SET
                        news_id = excluded.news_id,
                        symbol = excluded.symbol,
                        title = excluded.title,
                        summary = excluded.summary,
                        thumbnail_url = excluded.thumbnail_url,
                        news_category = excluded.news_category,
                        news_class = excluded.news_class,
                        published_at = excluded.published_at,
                        fetched_at = excluded.fetched_at,
                        expires_at = excluded.expires_at,
                        payload_json = excluded.payload_json
                    """,
                    (
                        news_id,
                        dedupe_key,
                        source,
                        symbol,
                        title,
                        summary,
                        url,
                        thumbnail_url,
                        news_category,
                        news_class,
                        published_at,
                        fetched_at,
                        expires_at,
                        payload_json,
                    ),
                )
                stored += 1
        return stored

    def list_news_cache(
        self,
        symbols: List[str] | None = None,
        sources: List[str] | None = None,
        categories: List[str] | None = None,
        classes: List[str] | None = None,
        limit: int = 50,
    ) -> List[Dict[str, object]]:
        query = """
            SELECT payload_json
            FROM news_cache
            WHERE expires_at >= ?
        """
        params: List[object] = [utc_now_iso()]
        normalized_symbols = [item.strip().upper() for item in (symbols or []) if item.strip()]
        normalized_sources = [item.strip().lower() for item in (sources or []) if item.strip()]
        normalized_categories = [item.strip().lower() for item in (categories or []) if item.strip()]
        normalized_classes = [item.strip().lower() for item in (classes or []) if item.strip()]

        if normalized_symbols:
            placeholders = ",".join("?" for _ in normalized_symbols)
            query += f" AND symbol IN ({placeholders})"
            params.extend(normalized_symbols)
        if normalized_sources:
            placeholders = ",".join("?" for _ in normalized_sources)
            query += f" AND source IN ({placeholders})"
            params.extend(normalized_sources)
        if normalized_categories:
            placeholders = ",".join("?" for _ in normalized_categories)
            query += f" AND news_category IN ({placeholders})"
            params.extend(normalized_categories)
        if normalized_classes:
            placeholders = ",".join("?" for _ in normalized_classes)
            query += f" AND news_class IN ({placeholders})"
            params.extend(normalized_classes)

        query += " ORDER BY published_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        with self._connect() as conn:
            cursor = conn.execute(query, tuple(params))
            rows = cursor.fetchall()
        results: List[Dict[str, object]] = []
        for row in rows:
            try:
                payload = json.loads(row[0])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                results.append(payload)
        return results

    def purge_expired_news_cache(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM news_cache
                WHERE expires_at < ?
                """,
                (utc_now_iso(),),
            )
            return int(cursor.rowcount)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection
