from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BuilderAgentSpec:
    name: str
    description: str
    hidden: bool = True


class BuilderAgentRegistry:
    """Internal-only builder agents for dynamic routing development.

    These identifiers must remain hidden from end-user facing workflows.
    """

    def __init__(self) -> None:
        # This registry exists only to support *optional* internal-plan visibility in
        # `DynamicAgentRouter` (when `include_internal_plan=True`). The portfolio
        # management runtime does not depend on these builders for execution.
        self._agents: Dict[str, BuilderAgentSpec] = {
            "level1_signals_builder": BuilderAgentSpec(
                name="level1_signals_builder",
                description="Builds normalized signal collection contracts.",
            ),
            "level2_research_builder": BuilderAgentSpec(
                name="level2_research_builder",
                description="Builds bullish/bearish research debate contracts.",
            ),
            "level3_trader_builder": BuilderAgentSpec(
                name="level3_trader_builder",
                description="Builds trade proposal contract generation.",
            ),
            "level4_risk_builder": BuilderAgentSpec(
                name="level4_risk_builder",
                description="Builds risk profile evaluation constraints.",
            ),
            "level5_manager_builder": BuilderAgentSpec(
                name="level5_manager_builder",
                description="Builds final decision and execution gate logic.",
            ),
            "trader_builder": BuilderAgentSpec(
                name="trader_builder",
                description="Builds cross-level dynamic trade routing.",
            ),
        }

    def get(self, name: str) -> BuilderAgentSpec:
        return self._agents[name]

    def all_names(self) -> List[str]:
        return list(self._agents.keys())
