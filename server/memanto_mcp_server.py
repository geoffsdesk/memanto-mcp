"""
Memanto MCP Server

Exposes memanto's typed semantic memory (remember / recall / answer)
as MCP tools, backed by Moorcheh's no-indexing semantic vector store.

Uses memanto's Python service layer directly (not the REST API), so this
process is the only thing that needs to run.

Required env: MOORCHEH_API_KEY (get one at https://console.moorcheh.ai/api-keys)
"""

from __future__ import annotations

import os
import sys
from typing import Any, Literal

# --- import-time dependency check (fail loud, fail clear) ---------------------
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.stderr.write(
        "memanto-mcp: missing dependency 'mcp'. Install with:\n"
        "    pip install mcp\n"
    )
    raise

try:
    from memanto.app.clients.moorcheh import MoorchehClient
    from memanto.app.constants import MemoryType, ProvenanceType
    from memanto.app.core import MemoryRecord
    from memanto.app.models.session import AgentCreate, AgentPattern
    from memanto.app.services.agent_service import AgentService
    from memanto.app.services.memory_read_service import MemoryReadService
    from memanto.app.services.memory_write_service import MemoryWriteService
except ImportError:
    sys.stderr.write(
        "memanto-mcp: missing dependency 'memanto'. Install with:\n"
        "    pip install memanto\n"
    )
    raise


# --- configuration ------------------------------------------------------------

API_KEY = os.environ.get("MOORCHEH_API_KEY")
if not API_KEY:
    sys.stderr.write(
        "memanto-mcp: MOORCHEH_API_KEY is not set. "
        "Get a key at https://console.moorcheh.ai/api-keys and export it before "
        "starting the MCP server.\n"
    )
    # Don't raise here — let the server boot so MCP host can show the tool list.
    # Tool calls will fail with a clear message.

VALID_MEMORY_TYPES = {
    "fact", "preference", "goal", "decision", "artifact", "learning",
    "event", "instruction", "relationship", "context", "observation",
    "commitment", "error",
}
VALID_PROVENANCES = {
    "explicit_statement", "inferred", "observed", "validated",
    "corrected", "imported",
}
VALID_PATTERNS = {p.value for p in AgentPattern}  # support | project | tool


# --- service singletons (lazy) ------------------------------------------------

_client: MoorchehClient | None = None
_write: MemoryWriteService | None = None
_read: MemoryReadService | None = None
_agents: AgentService | None = None


def _ensure_services() -> tuple[MemoryWriteService, MemoryReadService, AgentService]:
    global _client, _write, _read, _agents
    if not API_KEY:
        raise RuntimeError(
            "MOORCHEH_API_KEY is not set. Export it and restart the MCP server."
        )
    if _client is None:
        _client = MoorchehClient(API_KEY)
        _write = MemoryWriteService(_client)
        _read = MemoryReadService(_client)
        _agents = AgentService()  # defaults to ~/.memanto/agents/
    assert _write is not None and _read is not None and _agents is not None
    return _write, _read, _agents


# --- helpers ------------------------------------------------------------------

def _serialize_agent(agent: Any) -> dict[str, Any]:
    """AgentInfo → plain dict (datetimes → ISO strings)."""
    if hasattr(agent, "model_dump"):
        d = agent.model_dump()
    else:
        d = dict(agent)
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


def _validate(value: str, allowed: set[str], field: str) -> None:
    if value not in allowed:
        raise ValueError(
            f"Invalid {field}: {value!r}. Must be one of: {sorted(allowed)}"
        )


# --- MCP server ---------------------------------------------------------------

mcp = FastMCP("memanto")


@mcp.tool()
def memanto_remember(
    agent_id: str,
    content: str,
    memory_type: str = "fact",
    title: str | None = None,
    tags: list[str] | None = None,
    confidence: float = 0.8,
    source: str = "claude",
    provenance: str = "explicit_statement",
) -> dict[str, Any]:
    """Store a typed memory for an agent.

    Args:
        agent_id: Which agent's memory to write to (must already exist; create with memanto_create_agent).
        content: The memory content (1–10000 chars).
        memory_type: One of fact, preference, goal, decision, artifact, learning, event,
            instruction, relationship, context, observation, commitment, error.
        title: Optional short title; auto-derived from content if omitted.
        tags: Optional list of free-form tags for filtering on recall.
        confidence: Confidence score in [0.0, 1.0]; defaults to 0.8.
        source: Free-form source label (e.g. "claude", "user", a tool name).
        provenance: How the memory was obtained — explicit_statement, inferred,
            observed, validated, corrected, imported.

    Returns: dict with the stored memory's id and namespace.
    """
    _validate(memory_type, VALID_MEMORY_TYPES, "memory_type")
    _validate(provenance, VALID_PROVENANCES, "provenance")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")

    write, _, _ = _ensure_services()
    resolved_title = title or (f"{content[:50]}..." if len(content) > 50 else content)

    record = MemoryRecord(
        type=memory_type,  # type: ignore[arg-type]
        title=resolved_title,
        content=content,
        scope_type="agent",
        scope_id=agent_id,
        actor_id=agent_id,
        source=source,
        confidence=confidence,
        tags=tags or [],
        provenance=provenance,  # type: ignore[arg-type]
    )
    return write.store_memory(record)


@mcp.tool()
def memanto_recall(
    query: str,
    agent_id: str,
    memory_types: list[str] | None = None,
    tags: list[str] | None = None,
    limit: int = 10,
    min_confidence: float | None = None,
) -> dict[str, Any]:
    """Semantic search over an agent's memory.

    Args:
        query: Natural-language query.
        agent_id: Whose memory to search.
        memory_types: Optional filter by type(s).
        tags: Optional filter by tag(s).
        limit: Max results (default 10).
        min_confidence: Optional minimum confidence threshold.

    Returns: dict with search hits (content, score, metadata).
    """
    _, read, _ = _ensure_services()
    if memory_types:
        for mt in memory_types:
            _validate(mt, VALID_MEMORY_TYPES, "memory_types[*]")
    return read.search_memories(
        query=query,
        scope_type="agent",
        scope_id=agent_id,
        memory_types=memory_types,
        tags=tags,
        min_confidence=min_confidence,
        limit=limit,
    )


@mcp.tool()
def memanto_recall_as_of(
    query: str,
    agent_id: str,
    as_of_date: str,
    memory_types: list[str] | None = None,
    tags: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Recall memories as they existed at a specific date.

    Args:
        as_of_date: ISO 8601 date or datetime (e.g. '2026-01-15' or '2026-01-15T12:00:00Z').
    """
    _, read, _ = _ensure_services()
    return read.search_as_of(
        query=query,
        as_of_date=as_of_date,
        scope_type="agent",
        scope_id=agent_id,
        memory_types=memory_types,
        tags=tags,
        limit=limit,
    )


@mcp.tool()
def memanto_recall_current(
    query: str,
    agent_id: str,
    memory_types: list[str] | None = None,
    tags: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Recall only currently-active memories (excludes superseded, expired, deleted)."""
    _, read, _ = _ensure_services()
    return read.search_current_only(
        query=query,
        scope_type="agent",
        scope_id=agent_id,
        memory_types=memory_types,
        tags=tags,
        limit=limit,
    )


@mcp.tool()
def memanto_answer(query: str, agent_id: str) -> dict[str, Any]:
    """RAG-grounded answer using the agent's memory.

    Memanto retrieves relevant memories and synthesizes an answer with citations.
    Use this when the user wants a synthesized response, not raw search hits.
    """
    _, read, _ = _ensure_services()
    return read.generate_answer(
        query=query,
        scope_type="agent",
        scope_id=agent_id,
    )


@mcp.tool()
def memanto_create_agent(
    agent_id: str,
    description: str | None = None,
    pattern: str = "support",
) -> dict[str, Any]:
    """Create a new agent (provisions a dedicated Moorcheh namespace).

    Args:
        agent_id: Unique kebab-case identifier (e.g. 'customer-support', 'geoff-personal').
        description: Optional human description.
        pattern: One of support, project, tool. Default 'support'.
    """
    _validate(pattern, VALID_PATTERNS, "pattern")
    _, _, agents = _ensure_services()
    info = agents.create_agent(
        AgentCreate(agent_id=agent_id, description=description, pattern=pattern),  # type: ignore[arg-type]
        moorcheh_api_key=API_KEY,  # type: ignore[arg-type]
    )
    return _serialize_agent(info)


@mcp.tool()
def memanto_list_agents() -> dict[str, Any]:
    """List all agents this MCP server knows about."""
    _, _, agents = _ensure_services()
    result = agents.list_agents()
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return {"agents": [_serialize_agent(a) for a in result]}  # fallback


@mcp.tool()
def memanto_get_agent(agent_id: str) -> dict[str, Any] | None:
    """Get metadata for a single agent (or None if it doesn't exist)."""
    _, _, agents = _ensure_services()
    info = agents.get_agent(agent_id)
    return _serialize_agent(info) if info else None


@mcp.tool()
def memanto_delete_agent(agent_id: str) -> dict[str, str]:
    """Delete an agent and its memory namespace.

    DESTRUCTIVE: this removes the agent's stored memories. Confirm with the user
    before calling.
    """
    _, _, agents = _ensure_services()
    agents.delete_agent(agent_id)
    return {"status": "deleted", "agent_id": agent_id}


# --- entrypoint ---------------------------------------------------------------

def main() -> None:
    """Console entrypoint. Runs FastMCP over stdio (the transport Cowork and most MCP hosts expect)."""
    mcp.run()


if __name__ == "__main__":
    main()
