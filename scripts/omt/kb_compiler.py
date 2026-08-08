#!/usr/bin/env python3
"""kb_compiler — Application Knowledge Base compiler.

feature_kb_akb P0 (PROJECT.md v2.1): unified build =
  curated .meta/doc/omt++/*.kb.omt (EXCLUDING code.kb.omt)
  + AST skeleton (kb_ast_extract over src/agentx — class/contract/dep)
  + code.kb.omt concept-text overlay merge (overlay text wins; refs union)
  → .meta/.omt/kb.index.jsonl (UNBOUNDED — no size budget) + kb.ir.json

Index is unbounded by design (PROJECT §Budget policy): token cost is
per-query (scoped + capped in omt_kb_nav), not per-index. Drift detectors:
orphan overlay-key warning + orphan-ref error + duplicate-id error.

Stdlib-only. Grammar: OMT-HDL subset.
  record := '@' kind SP id (SP attr)* (SP ' : ' payload)?
  attr := k=v | k="v,v"
  curated kinds: doc, flow, feature, pattern, xref, gotcha
  code kinds (overlay): class, contract, dep
  metadata kinds: version, var, budget (not rendered to index)
"""
from __future__ import annotations

import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

import kb_ast_extract

REPO_ROOT = Path(__file__).resolve().parents[2]

KB_KINDS = (
    "version", "var", "budget",
    "doc", "flow", "feature", "pattern", "xref", "gotcha",
    "class", "contract", "dep",
)
CONTENT_KINDS = {"doc", "flow", "feature", "pattern", "xref", "gotcha"}
CODE_KINDS = ("class", "contract", "dep")
RID_RE = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$")

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "must", "should",
    "will", "would", "could", "may", "might", "shall", "can",
    "need", "require", "ensure", "verify", "confirm",
}

MAX_TEXT_LENGTH = 300

OVERLAY_NAME = "code.kb.omt"
KB_SRC_DIR = REPO_ROOT / ".meta" / "doc" / "omt++"
SRC_ROOT = REPO_ROOT / "src" / "agentx"
INDEX_OUT = REPO_ROOT / ".meta" / ".omt" / "kb.index.jsonl"
IR_OUT = REPO_ROOT / ".meta" / ".omt" / "kb.ir.json"


@dataclass
class KBRecord:
    id: str
    kind: str
    line: int
    src: str
    tags: list[str]
    text: str
    refs: list[str]
    tier: str


def split_payload(rest: str) -> tuple[str, str]:
    """Split attrs from payload at first ' : ' outside double quotes."""
    in_q = False
    for i, c in enumerate(rest):
        if c == '"':
            in_q = not in_q
        elif not in_q and rest.startswith(" : ", i):
            return rest[:i], rest[i + 3:]
    return rest, ""


def parse(text: str, errors: list[str] | None = None, src: str = "") -> list[KBRecord]:
    """Parse .kb.omt text into KBRecord list (content-bearing kinds only)."""
    if errors is None:
        errors = []
    records: list[KBRecord] = []

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        m = re.match(r"@([a-z]+)\s+(\S+)(.*)$", line)
        if not m:
            errors.append(f"kb.omt:{lineno}: malformed record: {raw.strip()[:60]}")
            continue

        kind, rid, rest = m.group(1), m.group(2), m.group(3)
        if kind not in KB_KINDS:
            errors.append(f"kb.omt:{lineno}: unknown kind '@{kind}'")
            continue

        # Skip metadata records (version, var, budget) — test fixture expects
        # parse() to only return content records.
        if kind in ("version", "var", "budget"):
            continue

        attr_src, payload = split_payload(rest.strip())
        attrs = _parse_attrs(attr_src.strip(), lineno, errors)

        tags_str = attrs.pop("tags", "")
        tags = [t.strip() for t in re.split(r"[, ]+", tags_str) if t.strip()] if tags_str else []

        refs_str = attrs.pop("refs", "")
        refs = [r.strip() for r in refs_str.split(",") if r.strip()] if refs_str else []

        tier = attrs.pop("tier", "core")

        records.append(KBRecord(
            id=f"{kind}.{rid}",
            kind=kind,
            line=lineno,
            src=src,
            tags=tags,
            text=payload.strip(),
            refs=refs,
            tier=tier,
        ))

    return records


def _parse_attrs(attr_src: str, lineno: int, errors: list[str]) -> dict[str, str]:
    """Parse k=v tokens via shlex."""
    if not attr_src:
        return {}
    attrs: dict[str, str] = {}
    try:
        tokens = shlex.split(attr_src, posix=True)
    except ValueError as e:
        errors.append(f"kb.omt:{lineno}: attr parse: {e}")
        return {}
    for tok in tokens:
        if "=" not in tok:
            errors.append(f"kb.omt:{lineno}: attr '{tok}' is not k=v")
            continue
        k, v = tok.split("=", 1)
        attrs[k] = v
    return attrs


def build_ir(records: list[KBRecord], src_path: str) -> dict:
    """Build internal representation."""
    return {
        "version": "akb_hdl.1",
        "generated_from": str(src_path),
        "records": [
            {
                "id": r.id,
                "kind": r.kind,
                "line": r.line,
                "tags": r.tags,
                "text": r.text,
                "refs": r.refs,
                "tier": r.tier,
            }
            for r in records
        ],
    }


def render_kb_index(records: list[KBRecord], src_path: str) -> str:
    """Render JSONL index (content records only)."""
    lines: list[str] = []
    for r in records:
        entry: dict = {
            "id": r.id,
            "kind": r.kind,
            "tags": r.tags,
            "text": r.text,
            "src": str(src_path),
            "line": r.line,
        }
        if r.refs:
            entry["refs"] = r.refs
        entry["tier"] = r.tier
        lines.append(json.dumps(entry))
    return "\n".join(lines) + "\n"


def validate_style(doc_id: str, text: str, errors: list[str]):
    """Validate non-human style: len ≤300, no stopwords."""
    if len(text) > MAX_TEXT_LENGTH:
        errors.append(f"KB:{doc_id}: text exceeds 300 chars ({len(text)})")

    text_lower = text.lower()
    words = re.findall(r"[a-zA-Z]+", text_lower)
    for word in words:
        if word in STOPWORDS:
            errors.append(f"KB:{doc_id}: keyword '{word}' in text")
            break  # Record at least one error; tests check count > 0


def check_refs(records: list[KBRecord], errors: list[str]):
    """Check refs resolve to existing ids."""
    all_ids = {r.id for r in records}
    for r in records:
        for ref in r.refs:
            if ref not in all_ids:
                errors.append(f"KB:{r.id}: unresolved ref '{ref}'")


def check_ids(records: list[KBRecord], errors: list[str]):
    """Check for duplicate IDs."""
    seen: dict[str, int] = {}
    for r in records:
        if r.id in seen:
            # Only report once per duplicated id
            if seen[r.id] == r.line:
                continue
            errors.append(f"KB:{r.id}: duplicate id (line {seen[r.id]})")
            continue
        seen[r.id] = r.line


# ---------------------------------------------------------------------------
# Unified build (feature_kb_akb P0)
# ---------------------------------------------------------------------------
def _curated_entry(r: KBRecord) -> dict:
    entry: dict = {
        "id": r.id,
        "kind": r.kind,
        "tags": r.tags,
        "text": r.text,
        "src": r.src,
        "line": r.line,
    }
    if r.refs:
        entry["refs"] = r.refs
    entry["tier"] = r.tier
    return entry


def build_index(
    kb_src_dir: Path, src_root: Path, repo_root: Path
) -> tuple[list[dict], list[str], list[str]]:
    """curated .kb.omt (excl. overlay) + AST skeleton + overlay merge.

    Returns (entries, warnings, errors); entries in kb.index.jsonl schema.
    Merge rules (PROJECT.md §Extraction contract):
      - overlay `text` overrides skeleton auto-text (full style lint — curated)
      - refs = union(skeleton, overlay), sorted
      - skeleton src/line/tags always win (drift-free)
      - un-curated skeleton records keep auto-text (length-checked only —
        identifiers are symbols, not prose: stopword lint is for curated text)
      - orphan overlay key (no skeleton id) → warning, record not emitted
      - unified duplicate-id + unresolved-ref checks → errors
    """
    warnings: list[str] = []
    errors: list[str] = []
    kb_src_dir = Path(kb_src_dir)
    src_root = Path(src_root)
    repo_root = Path(repo_root)

    entries: list[dict] = []

    # 1. curated records (overlay file EXCLUDED — merge source only)
    curated_files = sorted(
        f for f in kb_src_dir.glob("*.kb.omt") if f.name != OVERLAY_NAME
    )
    for f in curated_files:
        try:
            rel = f.relative_to(repo_root).as_posix()
        except ValueError:
            rel = f.as_posix()
        for r in parse(f.read_text(encoding="utf-8"), errors, src=rel):
            validate_style(r.id, r.text, errors)
            entries.append(_curated_entry(r))

    # 2. AST skeleton (code tier — ALL public classes, auto-text floor)
    skeleton, skel_warnings = kb_ast_extract.extract(src_root, repo_root)
    warnings.extend(skel_warnings)

    # 3. overlay parse (code.kb.omt — kinds class/contract/dep)
    overlay_path = kb_src_dir / OVERLAY_NAME
    overlay: dict[str, KBRecord] = {}
    if overlay_path.exists():
        for r in parse(overlay_path.read_text(encoding="utf-8"), errors, src=OVERLAY_NAME):
            overlay[r.id] = r

    # 4. merge skeleton × overlay
    merged_ids: set[str] = set()
    for skel in skeleton:
        ovl = overlay.get(skel["id"])
        if ovl is not None:
            merged_ids.add(skel["id"])
            validate_style(ovl.id, ovl.text, errors)
            skel = dict(skel)
            skel["text"] = ovl.text
            skel["refs"] = sorted(set(skel["refs"]) | set(ovl.refs))
        elif len(skel["text"]) > MAX_TEXT_LENGTH:
            errors.append(
                f"KB:{skel['id']}: auto-text exceeds {MAX_TEXT_LENGTH} ({len(skel['text'])})"
            )
        entries.append(skel)

    # 5. orphan overlay keys (drift detector: renamed/removed class)
    for oid in sorted(overlay):
        if oid not in merged_ids:
            warnings.append(
                f"kb_compiler: orphan overlay key '{oid}' — no matching skeleton record"
            )

    # 6. unified checks
    seen: set[str] = set()
    for e in entries:
        if e["id"] in seen:
            errors.append(f"KB:{e['id']}: duplicate id")
        seen.add(e["id"])
    all_ids = {e["id"] for e in entries}
    for e in entries:
        for ref in e.get("refs", []):
            if ref not in all_ids:
                errors.append(f"KB:{e['id']}: unresolved ref '{ref}'")

    return entries, warnings, errors


def _build_ir_unified(entries: list[dict], generated_from: str) -> dict:
    return {
        "version": "akb_hdl.1",
        "generated_from": generated_from,
        "records": [
            {
                "id": e["id"],
                "kind": e["kind"],
                "line": e["line"],
                "tags": e["tags"],
                "text": e["text"],
                "refs": e.get("refs", []),
                "tier": e["tier"],
            }
            for e in entries
        ],
    }


def _render_index(entries: list[dict]) -> str:
    return "\n".join(json.dumps(e) for e in entries) + "\n"


# -- CLI --
def main() -> int:
    """CLI: build (write index+IR) or check (report only)."""
    args = sys.argv[1:]
    if not args or args[0] not in ("build", "check"):
        print("Usage: kb_compiler.py <build|check>")
        return 2
    mode = args[0]

    entries, warnings, errors = build_index(KB_SRC_DIR, SRC_ROOT, REPO_ROOT)

    kinds: dict[str, int] = {}
    for e in entries:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    summary = ", ".join(f"{k}={n}" for k, n in sorted(kinds.items()))
    print(f"kb_compiler {mode}: {len(entries)} records ({summary})")

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"kb_compiler {mode}: {len(errors)} errors — outputs NOT written")
        return 1

    if mode == "build":
        INDEX_OUT.parent.mkdir(parents=True, exist_ok=True)
        INDEX_OUT.write_text(_render_index(entries), encoding="utf-8")
        IR_OUT.write_text(
            json.dumps(
                _build_ir_unified(entries, f"{KB_SRC_DIR}/*.kb.omt + {SRC_ROOT}"),
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        size = INDEX_OUT.stat().st_size
        print(f"wrote {INDEX_OUT} ({size} B, unbounded) + {IR_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
