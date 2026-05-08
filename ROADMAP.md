# Roadmap — what's missing for fully regulated deployments

The bundled skill ([`skills/memanto-memory/SKILL.md`](skills/memanto-memory/SKILL.md)) describes the discipline a memory layer needs to be safe inside a multi-tenant, regulated B2B agent. Some of that discipline is already enforced by the server. Some of it is enforced *by Claude following the skill* — and would be sturdier if the server enforced it directly.

This page is the honest gap list, ranked by leverage. Issues and PRs welcome on any of these.

## P0 — Structured citation fields

**What's missing.** The server has no `source_uri`, `source_span`, or `quote` fields on `MemoryRecord`. The skill currently teaches Claude to encode citations inside the free-text `content` (`SOURCE: <doc-id> §<section> "<quote>"`). That works, but it puts attribution in unstructured text where it can't be queried, validated, or migrated.

**Why it matters.** Regulated buyers — legal, finance, healthcare — won't trust a memory that can't be traced back to a specific span in a specific document. Harvey grades source quality independently from answer quality on BigLaw Bench precisely because confident-but-uncited synthesis is the dominant failure mode. Hebbia markets its Verifiable Fact Layer (every claim hover-traceable to a span) as a compliance asset. The pattern is industry-wide.

**What shipping it looks like.**

```python
class MemoryRecord:
    source_uri: str | None        # canonical pointer to the source doc/object
    source_span: SourceSpan | None # page, paragraph, char offset, or selector
    quote: str | None             # the verbatim text the memory derives from
    captured_at: datetime         # when the citation was captured
```

Plus: a `recall` filter for "memories with citations only", and a write-time validator that warns when `provenance="explicit_statement"` is set without a citation.

## P0 — Versioned mutations and redact

**What's missing.** No `update_memory`, no version history exposed to MCP, no `redact` operation. `delete_agent` exists but is destructive. The skill instructs Claude to write a new memory with `provenance="corrected"` and a content-level reference to the old one, but the audit story is still implicit.

**Why it matters.** Anthropic's own Claude Managed Agents Memory writes an immutable version on every mutation specifically so deployments can "audit who changed what and when… inspect or restore a prior snapshot, and… scrub sensitive content out of history with redact." Regulated tenants will ask for this on day one. PII redaction is also a GDPR/HIPAA-shaped requirement that can't be solved by "just don't store PII" — operators need a way to scrub after the fact.

**What shipping it looks like.**

- `memanto_update_memory(memory_id, ...)` — produces a new version, links to predecessor, marks predecessor superseded.
- `memanto_redact_memory(memory_id, fields=["content"])` — replaces content while preserving the version chain and metadata. Logs the redaction event.
- `memanto_history(memory_id)` — returns the version chain.
- Every write returns a stable `version_id` separate from `memory_id`.

## P1 — Pluggable storage backends

**What's missing.** Coupled to Moorcheh. Operators who can't or won't sign up for a vector-DB SaaS are stuck.

**Why it matters.** Self-hosted, air-gapped, and EU-only deployments are common asks in regulated B2B. A SQLite backend (with `sqlite-vec`) would unlock single-developer and on-prem use; a pgvector backend would unlock most enterprise deployments that already standardize on Postgres.

**What shipping it looks like.** Define a `MemoryStore` protocol with the methods `MoorchehClient` already implements (`upsert`, `query`, `as_of`, `delete`, `create_namespace`, `delete_namespace`). Move the Moorcheh implementation behind it as `MoorchehStore`. Add `SQLiteStore` and `PgVectorStore`. Pick the backend via env var (`MEMANTO_BACKEND=sqlite|moorcheh|pgvector`) or `.mcp.json` config.

## P1 — Tenancy as a first-class primitive

**What's missing.** The skill teaches Claude to use composite `agent_id` (`<tenant>:<workspace>:<actor>`) and to refuse cross-tenant recall. The server doesn't know what a tenant is — it sees an opaque string and trusts whatever Claude passes.

**Why it matters.** "Cross-tenant bleed" is the named highest-impact failure mode in multi-tenant RAG. For legal specifically, it's also a conflicts-of-interest event. Defense-in-depth says the *server* should refuse cross-tenant queries, not just the model. A server-side enforced boundary survives prompt injection that the model-side discipline does not.

**What shipping it looks like.**

- First-class `tenant_id` field on `MemoryRecord` and on every read tool.
- A `MEMANTO_TENANT_RESOLVER` hook (env var pointing to a JSON config or a function) that maps a session to its allowed tenant set. Reads outside that set fail at the server, before hitting the vector store.
- Optional row-level-security adapters for `PgVectorStore` so the database also enforces.

## P1 — HTTP transport

**What's missing.** Server runs over stdio only. Cowork and most local MCP hosts want stdio; remote hosts and multi-tenant deployments want HTTP/SSE.

**Why it matters.** Standalone MCP servers running as services need an HTTP entrypoint for orchestration, health checks, and shared deployment. FastMCP supports HTTP/SSE; flipping the transport is a small change but worth doing intentionally with auth.

**What shipping it looks like.** A `--transport {stdio,http}` flag on the entrypoint. When `http`, require a bearer token from `MEMANTO_AUTH_TOKEN` env. Document auth proxying for production.

## P2 — Structured tags and a tag schema

**What's missing.** Tags are free-form strings. The skill suggests conventions (`jurisdiction:NY`, `matter:4711`, `conflict-group:initech`), but the server doesn't validate.

**Why it matters.** Tag drift makes cross-cutting recall unreliable. A small schema layer — even just registered tag namespaces with allowed values — catches typos and enforces conventions at write time.

**What shipping it looks like.** Optional `MEMANTO_TAG_SCHEMA` JSON pointing to a dict of `{namespace: {"values": [...], "required": bool}}`. Writes validate; recall normalizes.

## P2 — Test suite with fixtures

**What's missing.** No published test suite. The skill makes claims about server behavior (cross-tenant refusal, temporal correctness, supersession) that should be exercised continuously.

**Why it matters.** This is the kind of project where regressions in scoping or temporal correctness are silent and load-bearing. A regression in `recall_as_of` returning future memories would be a quietly-disastrous bug.

**What shipping it looks like.** `pytest` suite with a `FakeStore` that implements `MemoryStore`, plus integration tests against `SQLiteStore` once it lands. Fixtures for the named scenarios in the skill: cross-tenant refusal, drafting-vs-research, supersession with citations.

## P3 — Observability

**What's missing.** No structured logs, no metrics, no audit log export.

**Why it matters.** Operators of production agentic systems need to answer "what did this agent recall and why" for any user-visible action. A built-in audit log endpoint (or exporter) makes that a configuration question, not a custom-engineering question.

**What shipping it looks like.** Structured JSON logs on every read and write (memory_id, version_id, agent_id, tenant_id, latency, source if internal). Optional OpenTelemetry exporter. `memanto_audit_log(since, until, agent_id?)` tool that returns the log slice.

## P3 — Skill variants

**What's missing.** One skill, written for the regulated B2B audience. The earlier consumer/personal version was replaced.

**Why it matters.** Single-developer use ("remember my dotfiles preference") and team-internal use ("remember our team's coding conventions") have different rules. The drafting/recall-vs-answer rule, for example, is overkill for personal use.

**What shipping it looks like.** A `skills/memanto-memory-personal/SKILL.md` for individual use, kept lean. The MCP host picks based on description triggers.

## How to think about priority

If you're building a regulated B2B agent on top of this *today*: structured citations (P0) and versioned mutations + redact (P0) are the two things you'll wish you had first. If you're shipping into self-hosted or air-gapped environments: pluggable storage (P1) is the unlock. If you're worried about prompt injection through memory: server-enforced tenancy (P1) is your defense-in-depth.

PRs welcome on any of these. For larger items (P0 / P1) please open an issue first to align on interface shape.
