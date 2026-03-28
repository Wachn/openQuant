from __future__ import annotations

import asyncio


class Scheduler:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start_if_enabled(self) -> None:
        if not self.enabled or self._running:
            return
        self._running = True

        async def _idle_loop() -> None:
            while self._running:
                await asyncio.sleep(1.0)

        self._task = asyncio.create_task(_idle_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "running": self._running,
            "heartbeat": "alive" if self._running else "idle",
        }
