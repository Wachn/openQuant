from __future__ import annotations


class LoopbackServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 1455) -> None:
        self.host = host
        self.port = port
        self.running = False

    async def ensure_running(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False
