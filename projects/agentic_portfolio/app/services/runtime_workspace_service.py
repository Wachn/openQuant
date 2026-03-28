from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

from app.domain.routing.models import RouteRequest, RouteSource, WorkflowType
from app.services.platform_service import PlatformService
from app.services.provider_gateway import ProviderGateway
from app.storage.sqlite_store import SQLiteStore


class RuntimeWorkspaceService:
    def __init__(
        self,
        store: SQLiteStore,
        platform: PlatformService,
        provider_gateway: ProviderGateway,
        suzy_activation_phrase: str,
        suzy_edit_root: Path,
    ) -> None:
        self.store = store
        self.platform = platform
        self.provider_gateway = provider_gateway
        self.suzy_activation_phrase = suzy_activation_phrase
        self.suzy_edit_root = suzy_edit_root.resolve()

    def create_session(self, title: str | None = None) -> dict[str, object]:
        session_id = str(uuid.uuid4())
        session_title = title or "SuzyBae Session"
        self.store.create_chat_session(
            session_id=session_id,
            title=session_title,
            metadata={"mode": "runtime", "agent": "SuzyBae", "orchestrator": "runtime-sisyphus"},
        )
        return {
            "session_id": session_id,
            "title": session_title,
            "state": "active",
        }

    def list_sessions(self) -> dict[str, object]:
        return {"sessions": self.store.list_chat_sessions()}

    def suzy_status(self) -> dict[str, object]:
        settings = self.store.get_settings()
        active = settings.get("suzy_self_edit_active", "false").lower() == "true"
        return {
            "active": active,
            "edit_root": str(self.suzy_edit_root),
        }

    def activate_suzy(self, command: str) -> dict[str, object]:
        if command != self.suzy_activation_phrase:
            raise ValueError("invalid activation command")
        self.store.set_setting("suzy_self_edit_active", "true")
        return {
            "active": True,
            "message": "Suzy self-edit mode activated",
        }

    def suzy_self_edit(self, file_path: str, find_text: str, replace_text: str) -> dict[str, object]:
        settings = self.store.get_settings()
        active = settings.get("suzy_self_edit_active", "false").lower() == "true"
        if not active:
            raise ValueError("suzy self-edit mode is not active")

        target = Path(file_path)
        if not target.is_absolute():
            target = self.suzy_edit_root / target
        target = target.resolve()

        try:
            target.relative_to(self.suzy_edit_root)
        except ValueError as exc:
            raise ValueError("file path outside allowed edit root") from exc

        if not target.exists() or not target.is_file():
            raise ValueError("file not found")

        source = target.read_text(encoding="utf-8")
        if find_text not in source:
            raise ValueError("find_text not found in file")

        updated = source.replace(find_text, replace_text, 1)
        target.write_text(updated, encoding="utf-8")
        return {
            "edited": True,
            "file_path": str(target),
            "replacements": 1,
        }

    def rename_session(self, session_id: str, title: str) -> dict[str, object]:
        normalized = title.strip()
        if not normalized:
            raise ValueError("title is required")
        renamed = self.store.rename_chat_session(session_id=session_id, title=normalized)
        if not renamed:
            raise ValueError("session not found")
        session = self.store.get_chat_session(session_id)
        if session is None:
            raise ValueError("session not found")
        return {"session": session}

    def delete_session(self, session_id: str) -> dict[str, object]:
        deleted = self.store.delete_chat_session(session_id)
        if not deleted:
            raise ValueError("session not found")
        return {"session_id": session_id, "deleted": True}

    def get_session(self, session_id: str) -> dict[str, object]:
        session = self.store.get_chat_session(session_id)
        if session is None:
            raise ValueError("session not found")
        messages = self.store.list_chat_messages(session_id)
        return {
            "session": session,
            "messages": messages,
        }

    def _should_attach_portfolio_context(self, message: str) -> bool:
        normalized = message.lower()
        keywords = (
            "my portfolio",
            "portfolio",
            "equity",
            "cash balance",
            "holdings",
            "allocation",
            "drawdown",
            "pnl",
        )
        return any(token in normalized for token in keywords)

    def _extract_symbol_tokens(self, message: str) -> list[str]:
        tokens = re.findall(r"\b[A-Z][A-Z0-9.=-]{1,9}\b", message.upper())
        deduped: list[str] = []
        for token in tokens:
            if token not in deduped:
                deduped.append(token)
        return deduped[:8]

    def _runtime_tracked_symbols(self, message: str) -> list[str]:
        snapshot = self.platform.latest_portfolio()
        from_positions = [item.symbol.upper() for item in snapshot.positions if item.symbol.strip()]
        mentioned = self._extract_symbol_tokens(message)
        merged: list[str] = []
        for symbol in [*mentioned, *from_positions]:
            normalized = symbol.strip().upper()
            if normalized and normalized not in merged:
                merged.append(normalized)
        return merged[:8] or ["AAPL", "MSFT", "NVDA"]

    def _portfolio_context_snippet(self, detailed: bool = False) -> str:
        snapshot = self.platform.latest_portfolio()
        positions = snapshot.positions[: (6 if detailed else 3)]
        if positions:
            position_summary = "; ".join(
                f"{item.symbol} qty={item.quantity:.4f} last={item.last_price:.2f}" for item in positions
            )
        else:
            position_summary = "none"
        return (
            "Portfolio snapshot: "
            f"equity={snapshot.equity:.2f}, cash={snapshot.cash:.2f}, daily_pnl={snapshot.daily_pnl:.2f}, drawdown={snapshot.drawdown:.4f}, positions={position_summary}."
        )

    def _augment_chat_message_with_runtime_context(
        self,
        message: str,
        workflow: WorkflowType,
        automation_enabled: bool,
    ) -> str:
        detailed = automation_enabled or self._should_attach_portfolio_context(message) or workflow in {
            WorkflowType.TRADE_CANDIDATE,
            WorkflowType.EXECUTE_TICKET,
        }
        try:
            context = self._portfolio_context_snippet(detailed=detailed)
        except Exception:
            return message
        return f"{message}\n\n{context}"

    def _build_runtime_portfolio_intel(self, message: str, automation_enabled: bool) -> dict[str, object]:
        tracked_symbols = self._runtime_tracked_symbols(message)
        monitor = self.platform.monitor_status()
        if automation_enabled and not bool(monitor.get("enabled", False)):
            monitor = self.platform.enable_monitor(tracked_symbols=tracked_symbols, interval_seconds=60)

        breakdown = self.platform.portfolio_breakdown(period="7d", frequency="daily")
        consultant = self.platform.consultant_brief(period="7d", frequency="daily")
        risk_memo = consultant.get("risk_memo") if isinstance(consultant, dict) else {}
        if not isinstance(risk_memo, dict):
            risk_memo = {}
        largest_position_pct = float(risk_memo.get("largest_position_pct", 0.0))
        drawdown_pct = float(risk_memo.get("drawdown_pct", 0.0))
        promotion_ready = bool(risk_memo.get("promotion_readiness", False))

        urgency = "low"
        urgency_reason = "portfolio_stable"
        if drawdown_pct <= -8.0 or largest_position_pct >= 55.0:
            urgency = "high"
            urgency_reason = "drawdown_or_concentration_breach"
        elif drawdown_pct <= -4.0 or largest_position_pct >= 35.0:
            urgency = "medium"
            urgency_reason = "rising_risk_conditions"

        recommendation = "hold_monitor"
        if urgency == "high":
            recommendation = "de_risk_sell_or_hedge"
        elif not promotion_ready:
            recommendation = "reduce_concentration_and_raise_cash"
        elif automation_enabled:
            recommendation = "run_trade_lane_and_rebalance"

        deterministic_chain: dict[str, object] | None = None
        if automation_enabled:
            cycle = self.platform.run_daily_cycle(tracked_symbols=tracked_symbols, period="7d", frequency="daily")
            deterministic_chain = {
                "mode": "auto_execution",
                "run_id": cycle.get("run_id"),
                "linked_runs": cycle.get("linked_runs", {}),
            }

        cached_news = self.platform.cached_news_feed(
            symbols=tracked_symbols,
            sources=["yahoo_finance", "investing_com", "reuters"],
            categories=None,
            classes=None,
            limit=12,
            focus_mode="focused",
        )
        cache_items = cached_news.get("items", []) if isinstance(cached_news, dict) else []
        if not isinstance(cache_items, list):
            cache_items = []
        if not cache_items:
            refreshed_news = self.platform.news_feed(
                symbols=tracked_symbols,
                sources=["yahoo_finance", "investing_com", "reuters"],
                categories=None,
                classes=None,
                limit=12,
                focus_mode="focused",
            )
            if isinstance(refreshed_news, dict):
                refreshed_items = refreshed_news.get("items", [])
                if isinstance(refreshed_items, list):
                    cache_items = refreshed_items

        return {
            "chain_mode": "auto_execution" if automation_enabled else "report_and_urgent_notify",
            "monitoring": {
                "enabled": bool(monitor.get("enabled", False)),
                "tracked_symbols": tracked_symbols,
                "last_cycle_at": monitor.get("last_cycle_at"),
                "cycles": int(monitor.get("cycles", 0)),
            },
            "management": {
                "breakdown_run_id": breakdown.get("run_id"),
                "consultant_run_id": consultant.get("run_id") if isinstance(consultant, dict) else None,
            },
            "recommendation": {
                "action": recommendation,
                "promotion_ready": promotion_ready,
            },
            "urgency": {
                "level": urgency,
                "reason": urgency_reason,
            },
            "deterministic_chain": deterministic_chain,
            "news_intel": {
                "cache_items": cache_items,
            },
        }

    def process_message(
        self,
        session_id: str,
        message: str,
        route_source: RouteSource,
        automation_enabled: bool,
        include_internal_plan: bool,
        agent_id: str,
        connection_id: str | None,
        variant: str,
        dynamic_router,
    ) -> dict[str, object]:
        session = self.store.get_chat_session(session_id)
        if session is None:
            raise ValueError("session not found")

        self.store.add_chat_message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=message,
            route=None,
            artifact=None,
        )

        decision = dynamic_router.route(
            RouteRequest(
                message=message,
                source=route_source,
                automation_enabled=automation_enabled,
                include_internal_plan=include_internal_plan,
            )
        )

        route_class = "deep_reasoning" if decision.workflow in {WorkflowType.TRADE_CANDIDATE, WorkflowType.EXECUTE_TICKET} else "fast_summary"
        if variant == "fast":
            route_class = "fast_summary"
        elif variant == "deep":
            route_class = "deep_reasoning"

        selected_model = self.provider_gateway.route_model(
            route_class,
            agent_id=agent_id,
            connection_id=connection_id,
        )

        provider_answer: dict[str, object] | None = None
        provider_error: str | None = None
        if route_source == RouteSource.CHAT:
            try:
                provider_message = self._augment_chat_message_with_runtime_context(
                    message=message,
                    workflow=decision.workflow,
                    automation_enabled=automation_enabled,
                )
                provider_answer = self.provider_gateway.generate_chat_response(
                    message=provider_message,
                    selected_model=selected_model,
                    session_id=session_id,
                )
            except Exception as exc:  # provider fallback remains explicit for operator visibility
                provider_error = f"{type(exc).__name__}:{exc}"

        workflow_payload: dict[str, object]
        assistant_text: str
        todos: list[str] = []
        if decision.workflow == WorkflowType.STARTUP_REPORT:
            workflow_payload = self.platform.startup_report(["AAPL", "MSFT", "NVDA"])
            assistant_text = "Startup report generated with latest market changes and suggestions."
            todos = ["Review startup suggestions", "Choose candidate to discuss or promote"]
        elif decision.workflow == WorkflowType.TRADE_CANDIDATE:
            workflow_payload = self.platform.run_trade_lane(symbol="AAPL", profile=self.platform.risk_profile())
            change_id = str(uuid.uuid4())
            self.store.upsert_change_request(
                change_id=change_id,
                status="pending",
                summary=f"Trade candidate for {workflow_payload['proposal']['symbol']}",
                payload={
                    "source": "runtime_workspace",
                    "run_id": workflow_payload["run_id"],
                    "ticket": workflow_payload["ticket"],
                },
                snooze_until=None,
            )
            workflow_payload["change_request_id"] = change_id
            assistant_text = "Trade candidate generated and stored as a pending change request."
            todos = ["Open change request", "Promote or snooze candidate"]
        elif decision.workflow == WorkflowType.EXECUTE_TICKET:
            workflow_payload = {
                "blocked": True,
                "reason": "Execution remains confirmation-gated via paper-submit endpoint.",
            }
            assistant_text = "Execution requires explicit confirmation through the ticket endpoint."
            todos = ["Review ticket", "Confirm via paper submit endpoint"]
        else:
            workflow_payload = self.platform.research_query(message)
            answer = workflow_payload.get("answer") if isinstance(workflow_payload, dict) else None
            if isinstance(answer, str) and answer.strip():
                assistant_text = answer.strip()
            else:
                assistant_text = "Research response generated with evidence bundle."
            todos = ["Review evidence", "Refine prompt for deeper analysis"]

        try:
            runtime_portfolio_intel = self._build_runtime_portfolio_intel(
                message=message,
                automation_enabled=automation_enabled,
            )
            workflow_payload["runtime_portfolio_intel"] = runtime_portfolio_intel
            urgency = ((runtime_portfolio_intel.get("urgency") or {}).get("level") if isinstance(runtime_portfolio_intel, dict) else None)
            if urgency == "high" and not automation_enabled:
                change_id = str(uuid.uuid4())
                self.store.upsert_change_request(
                    change_id=change_id,
                    status="pending",
                    summary="Urgent portfolio risk attention required",
                    payload={
                        "source": "runtime_workspace",
                        "reason": "high_urgency_risk",
                        "runtime_portfolio_intel": runtime_portfolio_intel,
                    },
                    snooze_until=None,
                )
                workflow_payload["urgent_change_request_id"] = change_id
        except Exception as exc:
            workflow_payload["runtime_portfolio_intel_error"] = f"{type(exc).__name__}:{exc}"

        if provider_answer is not None:
            workflow_payload["provider"] = provider_answer["provider"]
            workflow_payload["model"] = provider_answer["model"]
            workflow_payload["backend"] = provider_answer["backend"]
            workflow_payload["source"] = "provider_llm"
            if isinstance(provider_answer.get("reasoning"), str) and str(provider_answer.get("reasoning", "")).strip():
                workflow_payload["reasoning"] = str(provider_answer["reasoning"]).strip()
            assistant_text = str(provider_answer["answer"])
        elif provider_error is not None:
            workflow_payload["provider_error"] = provider_error
            if route_source == RouteSource.CHAT:
                assistant_text = f"Provider call failed: {provider_error}"

        thinking_text = decision.reason
        if isinstance(workflow_payload.get("reasoning"), str) and str(workflow_payload.get("reasoning", "")).strip():
            thinking_text = str(workflow_payload["reasoning"])

        assistant_count = sum(1 for msg in self.store.list_chat_messages(session_id) if msg.get("role") == "assistant")
        if assistant_count == 0:
            assistant_text = f"[oh-my-opencode-sisyphus] {assistant_text}"

        report = {
            "report_id": str(uuid.uuid4()),
            "session_id": session_id,
            "route": decision.workflow.value,
            "reason": decision.reason,
            "selected_model": selected_model,
            "agent": agent_id,
            "variant": variant,
            "orchestrator": "oh-my-opencode-sisyphus",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        message_artifact = {
            "decision": {
                "lane": decision.lane.value,
                "workflow": decision.workflow.value,
                "reason": decision.reason,
                "requires_user_confirmation": decision.requires_user_confirmation,
            },
            "report": report,
            "result": workflow_payload,
            "thinking": thinking_text,
            "todos": todos,
        }

        self.store.add_chat_message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=assistant_text,
            route=decision.workflow.value,
            artifact=message_artifact,
        )

        return {
            "assistant": assistant_text,
            "agent": agent_id,
            "variant": variant,
            "decision": message_artifact["decision"],
            "report": report,
            "result": {**workflow_payload, "todos": todos},
        }

    def list_change_requests(self, status: str | None = None) -> list[dict[str, object]]:
        return self.store.list_change_requests(status=status)

    def apply_change_request_action(
        self,
        change_id: str,
        action: str,
        snooze_minutes: int | None,
    ) -> dict[str, object]:
        existing = next((item for item in self.store.list_change_requests() if item["change_id"] == change_id), None)
        if existing is None:
            raise ValueError("change request not found")

        status = existing["status"]
        snooze_until = existing["snooze_until"]
        if action == "dismiss":
            status = "dismissed"
            snooze_until = None
        elif action == "promote":
            status = "promoted"
            snooze_until = None
        elif action == "remind":
            status = "pending"
            snooze_until = None
        elif action == "snooze":
            minutes = max(5, snooze_minutes or 60)
            status = "snoozed"
            snooze_until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
        else:
            raise ValueError("unsupported action")

        self.store.upsert_change_request(
            change_id=change_id,
            status=status,
            summary=existing["summary"],
            payload=existing["payload"],
            snooze_until=snooze_until,
        )
        updated = next((item for item in self.store.list_change_requests() if item["change_id"] == change_id), None)
        if updated is None:
            raise ValueError("change request not found")
        return updated
