# Runtime Agents

This folder defines runtime agent contracts used by the shipped application.

## Entry and Delegation Model

- `suzybae.md` is the main communication gateway agent for human interaction.
- `runtime_supervisor.md` owns route selection and safe handoff logic.
- Specialist runtime agents handle research, monitoring, planning, reporting, and critic roles.

Expected flow:

1. User interacts with `suzybae`.
2. `suzybae` routes or escalates to `runtime_supervisor` when needed.
3. `runtime_supervisor` delegates to specialist agents and returns a coherent response path.

## Required Metadata

Every runtime agent spec must include:

- `kind: runtime-agent`
- `tags` containing `runtime`
- `purpose`, `inputs`, `outputs`, `lane_access`, `restrictions`, `handoffs`

## Scope Boundary

- These files are runtime behavior contracts, not internal builder-agent definitions.
- Keep execution boundaries deterministic and confirmation-gated for execution-adjacent actions.
