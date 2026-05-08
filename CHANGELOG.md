# Changelog

## 0.2.0 — 2026-05-07

Initial public release.

- Nine MCP tools: `memanto_remember`, `memanto_recall`, `memanto_recall_current`, `memanto_recall_as_of`, `memanto_answer`, `memanto_create_agent`, `memanto_list_agents`, `memanto_get_agent`, `memanto_delete_agent`.
- Bundled Claude skill (`skills/memanto-memory/SKILL.md`) tailored for regulated B2B agents — composite `agent_id` scoping, drafting-vs-research recall rule, citation discipline, treat-memory-as-untrusted-on-read.
- Cowork plugin packaging (`.claude-plugin/plugin.json`, `.mcp.json`).
- Standalone runner via `pip install memanto-mcp` and the `memanto-mcp` console entry point (stdio transport).
- Backend: Moorcheh.

See [ROADMAP.md](ROADMAP.md) for what's next.

## 0.1.0 — internal

Internal pre-release. Generic memory skill, Cowork-only packaging.
