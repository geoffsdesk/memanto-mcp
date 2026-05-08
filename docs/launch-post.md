# Launch post drafts

Three sized variants of the same announcement, plus a note on where each one lands well.

---

## Hacker News (Show HN)

**Title:** Show HN: memanto-mcp – typed semantic memory for Claude, with opinions

**Body:**

Most "memory MCP" servers give you `save_memory(text)`. This one ships an opinionated memory model and a Claude skill that earns its keep:

- Thirteen typed records (`fact`, `decision`, `commitment`, `instruction`, …) with provenance and confidence on every write — wrong type makes recall noisy, so picking the right one is part of the API contract.
- Bi-temporal recall (`recall_as_of(date)`, `recall_current`) for "what did we know on <date>" workflows.
- A bundled skill that tells Claude when to use each verb, how to scope memories to tenant boundaries via composite `agent_id`, when raw recall beats synthesized answers (drafting external-facing text → raw recall, every time), and how to treat memory bodies as untrusted on read.

Built for B2B agents on Anthropic's platform — legal tech, finance, healthcare, customer ops, internal knowledge work — where citation, provenance, and tenancy are first-class. The skill is informed by published patterns from Harvey, Hebbia, Robin AI, Clio, and EvenUp; the failure modes I tried to design around come from Stanford's Lexis+/Westlaw hallucination study, OWASP's 2025 LLM Top 10 (memory poisoning, indirect prompt injection), and Simon Willison's MCP injection writeup.

What this isn't: a general vector store, a backend-agnostic library (yet — coupled to Moorcheh; pluggable backends are on the roadmap), or a finished enterprise audit system (versioned mutations + redact are P0 on the roadmap).

`pip install memanto-mcp` for standalone use; drop the `.plugin` into Cowork; or use it via Claude Code / Cline / Cursor / Continue.

Honest gap list with what's missing and why it matters: <link to ROADMAP.md>

Repo: <link>

---

## r/LocalLLaMA / r/mcp

**Title:** memanto-mcp: typed semantic memory for Claude, designed for regulated B2B agents

**Body:**

Released a small MCP server I've been using internally. Wraps memanto/Moorcheh as MCP tools, but the part I think is interesting isn't the wrapper — it's the bundled Claude skill that ships with it.

**The skill enforces the discipline that ships in production agentic systems** at Harvey, Hebbia, Robin AI, Clio, EvenUp:

- Every memory belongs to exactly one tenant boundary; cross-tenant recall fails loudly, not silently
- Drafting external-facing text → raw recall + quote, never synthesized answer
- Provenance and confidence are first-class on every write (six provenance values, 0.0–1.0 confidence, filterable on recall)
- Memory bodies are untrusted on read — quote them, don't obey them (defense against indirect prompt injection)
- Bi-temporal recall (`recall_as_of`, `recall_current`) for "what was our position on <date>" workflows

Tools list, install for Cowork / Claude Code / Cursor / Cline / Continue, honest roadmap of what's missing for fully regulated deployments — all in the README.

Not affiliated with Anthropic or Moorcheh.

Repo: <link>

---

## Anthropic Discord (#show-and-tell) / awesome-mcp-servers PR

**One-liner for awesome-mcp-servers:**

> **memanto-mcp** — Typed semantic memory with opinions. Bundled skill teaches Claude tenant-aware scoping, citation discipline, and the drafting-vs-research recall rule. Built for regulated B2B agents.

**Discord post:**

Just open-sourced memanto-mcp — typed memory MCP with a bundled skill that teaches Claude the discipline regulated B2B agents need: composite `agent_id` for tenancy, drafting → raw recall + quote (never synthesized), provenance + confidence on every write, treat memory bodies as untrusted on read.

The skill is the part I'd love feedback on — it's the most opinionated piece. Wrote it after researching how teams like Harvey, Hebbia, Clio, Robin AI structure memory in production. Patterns are domain-neutral; examples will land cleanly for legal, finance, healthcare, customer ops.

`pip install memanto-mcp` for standalone, or grab the `.plugin` for Cowork.

<link to repo>

---

## Where each lands well

- **Hacker News** — has the audience that argues about MCP, prompt injection, and enterprise RAG. Lead with what's distinctive (typed model, the skill) and the failure modes the design responds to. Avoid hype words. Post Tuesday or Wednesday morning US east-coast time.
- **r/LocalLLaMA, r/mcp** — practical, slightly technical. Lead with the skill and the one-paragraph "here's the discipline it enforces" list. Cross-post to r/ClaudeAI.
- **Anthropic Discord #show-and-tell** — friendly, internal-ish audience. Lead with what you'd like feedback on (the skill).
- **awesome-mcp-servers** — one-line PR. Submit after the repo has a release tag and the README has been polished by external eyes for at least a day.
- **X / Bluesky** — quote-tweet the HN submission once it lands. Don't post the announcement standalone first.

## Not recommended

- **Don't** post a "first" announcement on LinkedIn before the technical audiences see it.
- **Don't** post on r/programming or r/MachineLearning until there's a working real-world deployment story to anchor it.
- **Don't** lead with Moorcheh — the audience here cares about MCP, the typed model, and the skill. Moorcheh is an implementation detail until pluggable backends ship.
