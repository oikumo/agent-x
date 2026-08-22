"""Project-lifecycle state layer (feature_030.project_lifecycle, design_001 §1/§2).

Self-contained on purpose: env redirects are read PER CALL (tdd/state.py reads
them at import time — unusable for hermetic goldens from an already-imported
process). Truth = ledger records {kind:"project"|"project_link"} + filesystem
dirs; the manifest and Status headers are projections (synced, never truth).

Full-fold reader: project links span months — read_ledger_all() folds ALL
ledger-YYYYMM.jsonl archives + the hot file (analysis F1: latest+hot is
insufficient for long-lived project records).
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_CAP_BYTES = 64 * 1024

VALID_PROJECT_OPS = {"create", "close", "reopen", "archive"}
VALID_LINK_ORIGINS = {"scaffold", "inferred", "backfill", "manual"}
PROJECT_STATES = {"draft", "active", "complete", "archived"}


# --- lazy paths (env per call — hermetic-test substrate) ---------------------

def ledger_path() -> Path:
    env = os.environ.get("OMT_LEDGER_PATH")
    return Path(env) if env else REPO_ROOT / ".meta" / ".omt" / "ledger.jsonl"


def _ir_var(name: str) -> str | None:
    """IR @var override (state.py:42-56 idiom): env > IR > literal fallback."""
    try:
        ir = json.loads((REPO_ROOT / ".meta" / ".omt" / "harness.ir.json").read_text(encoding="utf-8"))
        value = ir.get("vars", {}).get(name)
        return str(value) if value is not None else None
    except (OSError, ValueError):
        return None


def projects_root() -> Path:
    env = os.environ.get("OMT_PROJECTS_ROOT")
    if env:
        return Path(env)
    irv = _ir_var("projects_root")
    return (REPO_ROOT / irv) if irv else REPO_ROOT / ".projects" / "meta"


def projects_archive() -> Path:
    env = os.environ.get("OMT_PROJECTS_ARCHIVE")
    if env:
        return Path(env)
    irv = _ir_var("projects_archive")
    return (REPO_ROOT / irv) if irv else REPO_ROOT / ".projects" / "archive"


def manifest_path() -> Path:
    return projects_root() / "META.md"


def templates_dir() -> Path:
    return REPO_ROOT / ".meta" / "templates"


# --- ledger IO (full fold) ---------------------------------------------------

def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        s = line.strip()
        if not s:
            continue
        try:
            records.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    return records


def read_ledger_all() -> list[dict]:
    """ALL archives (oldest first) + hot file, chronological."""
    hot = ledger_path()
    archives = sorted(hot.parent.glob("ledger-[0-9][0-9][0-9][0-9][0-9][0-9].jsonl"))
    records: list[dict] = []
    for arc in archives:
        records += _read_jsonl(arc)
    return records + _read_jsonl(hot)


def write_record(record: dict) -> None:
    hot = ledger_path()
    hot.parent.mkdir(parents=True, exist_ok=True)
    with open(hot, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **record}) + "\n")
    try:
        if hot.stat().st_size > LEDGER_CAP_BYTES:
            archive = hot.parent / f"ledger-{datetime.now(timezone.utc):%Y%m}.jsonl"
            with open(archive, "a", encoding="utf-8") as out:
                out.write(hot.read_text(encoding="utf-8"))
            hot.write_text("", encoding="utf-8")
    except OSError:
        pass  # rotation is best-effort (state.py R4 precedent)


# --- derivations --------------------------------------------------------------

def project_events(records: list[dict], slug: str) -> list[dict]:
    return [r for r in records if r.get("kind") == "project" and r.get("project") == slug]


def derive_links(records: list[dict]) -> dict[str, dict]:
    """Latest-wins per feature: {feature: {project, origin, ts}}."""
    links: dict[str, dict] = {}
    for r in records:
        if r.get("kind") == "project_link" and r.get("feature") and r.get("project"):
            links[r["feature"]] = {
                "project": r["project"], "origin": r.get("origin", "manual"), "ts": r.get("ts", ""),
            }
    return links


def duplicate_links(records: list[dict]) -> list[tuple[str, str]]:
    """(project, feature) pairs written more than once (writers must be idempotent)."""
    seen: dict[tuple[str, str], int] = {}
    for r in records:
        if r.get("kind") == "project_link" and r.get("feature") and r.get("project"):
            key = (r["project"], r["feature"])
            seen[key] = seen.get(key, 0) + 1
    return sorted(k for k, n in seen.items() if n > 1)


def derive_state(slug: str, records: list[dict], links: dict[str, dict]) -> str:
    events = project_events(records, slug)
    if not events:
        return "unknown"
    last_op = events[-1].get("op")
    if last_op == "close":
        return "complete"
    if last_op == "archive":
        return "archived"
    if last_op in ("create", "reopen"):
        return "active" if any(l["project"] == slug for l in links.values()) else "draft"
    return "unknown"


def project_of(feature: str, records: list[dict]) -> str | None:
    link = derive_links(records).get(feature)
    return link["project"] if link else None


def homes() -> list[str]:
    root = projects_root()
    if not root.is_dir():
        return []
    return sorted(d.name for d in root.iterdir() if d.is_dir())


# --- projections --------------------------------------------------------------

_STATUS_RE = re.compile(r"(> Status: \*\*)([a-z]+)(\*\*)")


def parse_status_header(project_md: Path) -> str | None:
    if not project_md.exists():
        return None
    m = _STATUS_RE.search(project_md.read_text(encoding="utf-8"))
    return m.group(2) if m else None


def sync_status_header(project_md: Path, state: str) -> bool:
    """Flip ONLY the `**<state>**` span; unparseable → False (never corrupt prose)."""
    if not project_md.exists():
        return False
    text = project_md.read_text(encoding="utf-8")
    new, n = _STATUS_RE.subn(rf"\g<1>{state}\g<3>", text, count=1)
    if n == 0:
        return False
    project_md.write_text(new, encoding="utf-8")
    return True


def normalize_status_header(project_md: Path, state: str) -> bool:
    """Legacy free-text `> Status: <prose>` → machine form `> Status: **<state>** · <prose>`.
    Only the Status line (first 5 lines) is rewritten; content is preserved."""
    if not project_md.exists():
        return False
    lines = project_md.read_text(encoding="utf-8").split("\n")
    for i, ln in enumerate(lines[:5]):
        if ln.startswith("> Status:") and not _STATUS_RE.search(ln):
            rest = ln.split("Status:", 1)[1].strip()
            if rest.startswith("**"):  # unwrap a leading **version** span as a pair
                closing = rest.find("**", 2)
                if closing > 0:
                    rest = (rest[2:closing] + rest[closing + 2:]).strip()
            rest = rest.strip("*").strip().lstrip("·—- ").strip()
            lines[i] = f"> Status: **{state}**" + (f" · {rest}" if rest else "")
            project_md.write_text("\n".join(lines), encoding="utf-8")
            return True
    return False


def manifest_rows(records: list[dict], links: dict[str, dict]) -> tuple[list[str], list[str]]:
    """(active_rows, archived_rows) for the GENERATED manifest."""
    active, archived = [], []
    for slug in homes():
        state = derive_state(slug, records, links)
        events = project_events(records, slug)
        created = events[0].get("ts", "—")[:10] if events else "—"
        last = events[-1].get("ts", "—")[:10] if events else "—"
        feats = sorted(f for f, l in links.items() if l["project"] == slug)
        feat_cell = ", ".join(feats) if feats else "—"
        if state == "archived":
            continue  # archived homes moved out of projects_root — listed from records below
        active.append(f"| {slug} | {state} | {feat_cell} | {created} | {last} |")
    seen_archived: set[str] = set()
    for r in records:
        if r.get("kind") == "project" and r.get("op") == "archive" and r.get("project"):
            slug = r["project"]
            seen_archived.add(slug)
    for slug in sorted(seen_archived):
        if derive_state(slug, records, links) == "archived":
            dest = next(
                (r.get("archived_to", "") for r in reversed(records)
                 if r.get("kind") == "project" and r.get("op") == "archive" and r.get("project") == slug),
                "",
            )
            archived.append(f"| {slug} | {dest or '.projects/archive/' + slug} |")
    return active, archived


def build_manifest(records: list[dict], links: dict[str, dict]) -> str:
    active, archived = manifest_rows(records, links)
    lines = [
        "# .projects/ — Project Homes (GENERATED)",
        "",
        "> GENERATED by `uv run scripts/omt/project.py sync` — do not hand-edit.",
        "> Truth: ledger `project`/`project_link` records + filesystem dirs.",
        "> Convention: `.projects/meta/<slug>/{PROJECT.md, CURRENT_STATE.md}` —",
        "> PROJECT.md canonical; CURRENT_STATE.md session log (newest on top).",
        "",
        "| project | state | features | created | last event |",
        "|---|---|---|---|---|",
        *(active or ["| _(none)_ | — | — | — | — |"]),
    ]
    if archived:
        lines += ["", "## Archived", "", "| project | archived_to |", "|---|---|", *archived]
    return "\n".join(lines) + "\n"
