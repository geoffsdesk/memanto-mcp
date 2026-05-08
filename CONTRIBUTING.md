# Contributing

Thanks for considering a contribution. A few notes before you open a PR.

## What's most useful right now

The two highest-leverage contributions are tracked at the top of [ROADMAP.md](ROADMAP.md):

1. **Structured citation fields** (`source_uri`, `source_span`, `quote`) on `MemoryRecord`.
2. **Versioned mutations + redact** — `update_memory`, `redact_memory`, `history`, immutable version IDs.

Both should land behind feature flags; the existing API stays compatible.

After those: pluggable storage backends (SQLite, pgvector) and server-enforced tenancy.

## Before you start

- For anything in **P0 or P1** on the roadmap, open an issue first so we can align on the interface shape. These are load-bearing changes and we'd rather discuss the shape than rewrite a PR.
- For **P2 / P3** work, smaller doc fixes, or skill improvements, just send a PR.

## Local development

```bash
git clone https://github.com/geoffsdesk/memanto-mcp
cd memanto-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export MOORCHEH_API_KEY="mch_..."
memanto-mcp     # starts the server on stdio
```

## Tests

There isn't a published test suite yet — that's [P2 on the roadmap](ROADMAP.md#p2--test-suite-with-fixtures). If your PR adds testable behavior (especially around scoping, supersession, or temporal recall), please include `pytest` tests against a `FakeStore` even if the broader suite isn't in place yet. Bootstrapping that suite is itself a welcome contribution.

## Style

- Type hints on all public functions.
- `ruff` and `black` defaults.
- Tool docstrings are user-facing — they're what the model sees. Keep them precise. Anthropic's [Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents) is the reference.

## The skill

Changes to [`skills/memanto-memory/SKILL.md`](skills/memanto-memory/SKILL.md) are governance changes, not just doc changes — Claude follows what's in there. PRs that add or remove rules should explain the failure mode they prevent or enable, ideally with a concrete reference (a published incident, a vendor pattern, an Anthropic engineering post).

## Code of conduct

Be the kind of person you'd want to work with. We don't have a long policy; this isn't a hostile place. If something feels off, open an issue.

## License

By contributing, you agree your contributions will be licensed under the MIT License.
