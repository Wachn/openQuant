# Runtime Agents (v2.0)

These files define the agent system that lives **inside the shipped application**.

Required metadata:
- `kind: runtime-agent`
- `tags` must include `runtime`

These are not builder agents.
Do not place them under `.opencode/internal_builders/`.

Primary runtime entry agents:

- `suzybae.md` (main frontend chat agent)
- `runtime_supervisor.md` (runtime-sisyphus orchestration supervisor)
- `oh_my_opencode_bridge_agent.md` (OpenCode-style command/keybind bridge behavior)
