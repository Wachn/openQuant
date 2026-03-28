# Skill: Anthropic Skill Patterns

Use when creating or adapting reusable OpenCode skills from external skill libraries.

## Required capabilities

- keep each skill narrowly scoped
- describe both what the skill does and when to trigger it
- keep instructions concise and stepwise
- move bulky examples or assets into side files when needed
- prefer reusable workflows over one-off prompts

## Repository adaptation

Anthropic's `skills/` repository organizes one skill per folder with a main `SKILL.md` and optional support files.

For this repo, adapt that pattern into `.opencode/skills/*.md` by:

- using a clear skill title
- starting with a one-line trigger sentence
- listing required capabilities
- capturing product-specific adaptation rules
- referencing supporting repo files only when necessary

## Use in this project

Apply this pattern when adding skills for:

- runtime dashboard recovery
- provider/model routing
- OpenStock watchlist and monitoring workflows
- OpenClaw-style workspace settings and cron operations
- portfolio research and promotion flows
