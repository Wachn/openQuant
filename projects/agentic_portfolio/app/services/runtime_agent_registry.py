from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeAgentSpec:
    agent_id: str
    name: str
    kind: str
    tags: list[str]
    purpose: str
    lane_access: list[str]
    valid: bool
    errors: list[str]


class RuntimeAgentRegistry:
    def __init__(self, runtime_agents_dir: Path) -> None:
        self.runtime_agents_dir = runtime_agents_dir

    def list_specs(self) -> list[RuntimeAgentSpec]:
        if not self.runtime_agents_dir.exists():
            return []
        specs: list[RuntimeAgentSpec] = []
        for path in sorted(self.runtime_agents_dir.glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            specs.append(self._parse_file(path))
        return specs

    def validation_summary(self) -> dict[str, object]:
        specs = self.list_specs()
        invalid = [spec for spec in specs if not spec.valid]
        return {
            "runtime_agents_dir": str(self.runtime_agents_dir.resolve()),
            "count": len(specs),
            "valid": len(invalid) == 0,
            "invalid_count": len(invalid),
            "invalid_agents": [
                {"agent_id": spec.agent_id, "errors": spec.errors}
                for spec in invalid
            ],
        }

    def _parse_file(self, path: Path) -> RuntimeAgentSpec:
        lines = path.read_text(encoding="utf-8").splitlines()
        name = ""
        kind = ""
        purpose = ""
        tags: list[str] = []
        lane_access: list[str] = []

        collecting_tags = False
        collecting_lanes = False

        for raw in lines:
            line = raw.rstrip()
            stripped = line.strip()
            if stripped.startswith("name:"):
                name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("kind:"):
                kind = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("purpose:"):
                purpose = stripped.split(":", 1)[1].strip()

            if stripped.startswith("tags:"):
                collecting_tags = True
                collecting_lanes = False
                continue
            if stripped.startswith("lane_access:"):
                collecting_lanes = True
                collecting_tags = False
                continue

            if stripped and not stripped.startswith("-") and not stripped.startswith("#"):
                if collecting_tags and not stripped.startswith("tags:"):
                    collecting_tags = False
                if collecting_lanes and not stripped.startswith("lane_access:"):
                    collecting_lanes = False

            if collecting_tags and stripped.startswith("-"):
                tags.append(stripped[1:].strip())
            if collecting_lanes and stripped.startswith("-"):
                lane_access.append(stripped[1:].strip())

        errors: list[str] = []
        if kind != "runtime-agent":
            errors.append("kind must be runtime-agent")
        if "runtime" not in tags:
            errors.append("tags must include runtime")
        if not name:
            errors.append("name is required")
        if not purpose:
            errors.append("purpose is required")

        return RuntimeAgentSpec(
            agent_id=path.stem,
            name=name or path.stem,
            kind=kind,
            tags=tags,
            purpose=purpose,
            lane_access=lane_access,
            valid=len(errors) == 0,
            errors=errors,
        )
