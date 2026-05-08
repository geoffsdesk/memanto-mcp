# memanto-mcp

**Typed semantic memory for Claude. Memory with opinions, designed for regulated B2B agents.**

Most "memory MCP" servers give you `save_memory(text)` and call it done. This one ships an opinionated memory model — typed records (`fact`, `decision`, `commitment`, `instruction`, …), provenance and confidence on every write, tenant-aware scoping, and bi-temporal recall — together with a Claude skill that tells the model *when* to remember vs. recall vs. answer, and how to keep citations and tenancy clean.

If you're building B2B agents on Anthropic's platform — legal tech, finance, healthcare, customer ops, internal knowledge work — that's the audience this is built for.

## What's distinctive

- **Typed memory.** Thirteen first-class memory types (`fact`, `preference`, `goal`, `decision`, `commitment`, `instruction`, `relationship`, `context`, `observation`, `event`, `artifact`, `learning`, `error`). Wrong type = noisy recall. Picking the right type is part of the API contract.
- **Provenance and confidence on every record.** `explicit_statement` / `inferred` / `observed` / `validated` / `corrected` / `imported`, plus a 0.0–1.0 confidence score. Filterable on recall via `min_confidence`. The audit trail is in the data, not bolted on.
- **Bi-temporal reads.** `recall_as_of(date)` returns memory as it stood on a date; `recall_current` excludes superseded/expired records. Built for "what did we know on <date>" workflows.
- **A bundled Claude skill that earns its keep.** [`skills/memanto-memory/SKILL.md`](skills/memanto-memory/SKILL.md) tells Claude when to use each verb, how to scope memories to tenant boundaries via composite `agent_id`, when raw recall beats synthesized answers (drafting external-facing text → raw recall, every time), and how to treat memory bodies as untrusted on read.
- **One process.** Wraps the [memanto](https://github.com/moorcheh-ai/memanto) Python service layer directly — no separate REST process to run.

## What this is not

- Not a general-purpose vector store. Memories are short, structured, and typed; if you need to index 100k contracts, do that in your document store and use this for the *decisions, commitments, and observations* the agent makes about them.
- Not backend-agnostic (yet). Currently coupled to [Moorcheh](https://moorcheh.ai) as the vector backend. Free tier is 100k ops/month; pluggable backends are on the [roadmap](ROADMAP.md).
- Not an enterprise audit system. The skill is opinionated about what regulated deployments need; the server doesn't yet enforce all of it. See the [roadmap](ROADMAP.md) for the gaps.

## Tools

Nine MCP tools, namespaced under `memanto`:

| Tool                       | Purpose                                                  |
| -------------------------- | -------------------------------------------------------- |
| `memanto_remember`         | Store a typed memory (fact, preference, goal, decision, …) |
| `memanto_recall`           | Semantic search over an agent's memory                   |
| `memanto_recall_current`   | Recall only currently-active (non-superseded) memories   |
| `memanto_recall_as_of`     | Recall as of a specific date                             |
| `memanto_answer`           | RAG-grounded answer using memanto's built-in LLM         |
| `memanto_create_agent`     | Provision a new agent (creates a Moorcheh namespace)     |
| `memanto_list_agents`      | List known agents                                        |
| `memanto_get_agent`        | Get a single agent's metadata                            |
| `memanto_delete_agent`     | Delete an agent and all its memory (destructive)         |

## Install

### As a Cowork plugin (Anthropic's Cowork mode)

1. Download the latest [`memanto-mcp.plugin`](https://github.com/geoffsdesk/memanto-mcp/releases/latest) release.
2. Drop it into Cowork via the plugin install UI.
3. Set `MOORCHEH_API_KEY` in the environment Cowork inherits, then restart Cowork.

### As a standalone MCP server (Claude Code, Cline, Cursor, Continue, …)

```bash
pip install memanto-mcp
export MOORCHEH_API_KEY="mch_..."
```

Then point your MCP host at the binary. Claude Code:

```bash
claude mcp add memanto -- memanto-mcp
```

Cursor / Cline / Continue: add to your MCP config as a stdio server with command `memanto-mcp`.

For the bundled skill to load in MCP hosts that support skills (Cowork, Claude Code with the skills plugin), copy [`skills/memanto-memory/SKILL.md`](skills/memanto-memory/SKILL.md) into the host's skills directory.

### Get a Moorcheh API key

Sign up at <https://console.moorcheh.ai/api-keys>. Free tier is 100k ops/month.

## First run

```
> Create a memanto agent called acme:matter-4711:user-jdoe and remember
> that this matter has a 60-day notice period.
```

Claude calls `memanto_create_agent` then `memanto_remember(memory_type="fact", content="Matter 4711 (Acme): 60-day notice period.", confidence=0.95)`.

```
> What do we know about Matter 4711?
```

Claude calls `memanto_recall(query="Matter 4711", agent_id="acme:matter-4711:user-jdoe")` and quotes the stored fact.

```
> What was our position on Matter 4711 before the redesign on 2026-03-01?
```

Claude calls `memanto_recall_as_of(query="Matter 4711 position", agent_id=..., as_of_date="2026-02-28")`.

## How the skill thinks about scoping

The server uses `agent_id` as the scoping primitive. The skill teaches Claude to treat it as a composite key:

```
agent_id = "<tenant>:<workspace>:<actor>"
```

For example: `acme:matter-4711:user-jdoe`. Cross-tenant recall is the highest-impact failure mode in production memory systems — the skill makes Claude refuse it loudly rather than silently returning empty results when the boundary is wrong.

For axes that don't fit the composite key (jurisdiction, region, conflict-of-interest group, product line), use `tags` — they're filterable on recall.

## Drafting rule

When the user is composing **external-facing text** — a contract amendment, a customer-facing email, a regulatory filing, a clinical summary, a briefing memo — the skill instructs Claude to use `memanto_recall` (raw hits) and quote, not `memanto_answer` (synthesized). The audit cost of a paraphrased citation is too high.

When the user is researching, exploring, or briefing themselves, `memanto_answer` is fine.

## Roadmap

The honest gaps — what the skill assumes you'd want in a fully regulated deployment and what the server doesn't do yet — are documented in [ROADMAP.md](ROADMAP.md). Highlights: structured `source_uri` + `source_span` fields (citations currently get encoded inside `content`), versioned mutations + redact API, pluggable storage backends, and an HTTP transport for non-stdio hosts.

## Repository layout

```
memanto-mcp/
├── .claude-plugin/plugin.json       # Cowork plugin manifest
├── .mcp.json                        # MCP server registration (Cowork)
├── server/memanto_mcp_server.py     # FastMCP server (stdio)
├── skills/memanto-memory/SKILL.md   # the bundled skill
├── pyproject.toml                   # for `pip install memanto-mcp`
├── README.md                        # this file
├── ROADMAP.md                       # what's missing, ranked
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE                          # MIT
└── docs/
    └── launch-post.md               # cross-post draft
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The two highest-leverage contributions right now are (1) a pluggable storage backend (interface + a SQLite or pgvector implementation) and (2) a structured citation model (`source_uri` + `source_span` + `quote`). Both are on the [roadmap](ROADMAP.md).

## License

MIT. See [LICENSE](LICENSE).

## Credits

- [memanto](https://github.com/moorcheh-ai/memanto) and [Moorcheh](https://moorcheh.ai) — the typed memory model and vector backend this wraps.
- [Anthropic's MCP](https://modelcontextprotocol.io) and [Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — the protocol and skill format.
- The teams shipping enterprise agentic systems whose published patterns informed the skill: Harvey, Hebbia, Robin AI, Clio, EvenUp, Casetext.

Not affiliated with Anthropic or Moorcheh.
