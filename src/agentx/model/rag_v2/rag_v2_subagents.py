"""RagV2 subagents — the chunk-analyst SubAgent dict spec (feature_027).

Per design_001 §rag_v2_subagents: the ``chunk-analyst`` is dispatched via the
deepagents built-in ``task({subagentType, description})`` tool; it reads a
single retrieved chunk file from the agent backend and returns a concise
structured summary (summary + citation + entities).

Per Constraint (b): ``subagents=[chunk-analyst]`` coexists with the
auto-added ``general-purpose`` default (``create_deep_agent`` adds it unless
v2 disables it via ``GeneralPurposeSubagentProfile(enabled=False)``). v2 KEEPS
general-purpose (less surface-area change).
"""

from __future__ import annotations

# The chunk-analyst subagent — one-file summarize, dispatched via the
# deepagents built-in task({subagentType, description}) tool. Per the LangChain
# subagents doc (docs.langchain.com/oss/python/deepagents/subagents) the
# SubAgent dict spec is {name, description, system_prompt, tools?,
# middleware?, skills?, response_format?, permissions?}.
CHUNK_ANALYST: dict = {
    "name": "chunk-analyst",
    "description": (
        "Reads a single retrieved chunk file from the agent backend and "
        "returns a concise structured summary: the chunk's key claims, "
        "the source citation, and any named entities. One chunk per call."
    ),
    "system_prompt": (
        "You are a chunk-analyst subagent. You are given a single chunk "
        "file path in the agent backend filesystem. Read it with read_file, "
        "then return a JSON object with keys: summary (str, 1-3 sentences), "
        "citation (str, the source path + page/line), entities (list of "
        "str). Do NOT read multiple files; do NOT search. Be concise."
    ),
    # tools omitted → inherits the deepagents built-in read_file/grep/glob.
    # response_format omitted → returns free text (the orchestrator parses).
    # permissions omitted → default.
}

# The full subagent list passed to create_deep_agent(subagents=...).
# create_deep_agent AUTO-ADDS the general-purpose default alongside this
# list UNLESS v2 disables it (GeneralPurposeSubagentProfile(enabled=False)).
# v2 KEEPS general-purpose (Constraint b) — less surface-area change.
RAG_V2_SUBAGENTS: list[dict] = [CHUNK_ANALYST]
