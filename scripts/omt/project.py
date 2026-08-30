#!/usr/bin/env python3
"""OMT++ project-lifecycle CLI (feature_030.project_lifecycle, design_001 §3).

A project is a first-class entity: create → iterate → spawn features (for it or
another) → close → archive. OMT phases stay feature-only; `.projects/` stays
non-gated. This CLI is the single writer of project lifecycle records and of
the GENERATED `.projects/meta/META.md` manifest; `harnessc check` verifies.

Usage:
    uv run scripts/omt/project.py new "<name>" [--slug s]
    uv run scripts/omt/project.py link <feature> <project> [--origin manual]
    uv run scripts/omt/project.py log <slug> "<note>"
    uv run scripts/omt/project.py status [slug]
    uv run scripts/omt/project.py close <slug> [--force] [--archive]
    uv run scripts/omt/project.py reopen <slug>
    uv run scripts/omt/project.py archive <slug>
    uv run scripts/omt/project.py sync
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # importlib-safe (test loaders)
import project_state as ps


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    if not slug:
        raise SystemExit("error: project name produces an empty slug")
    return slug


def _render(template: str, mapping: dict[str, str]) -> str:
    text = (ps.templates_dir() / template).read_text(encoding="utf-8")
    for key, val in mapping.items():
        text = text.replace("{{" + key + "}}", val)
    return text


def _sync_all() -> list[str]:
    """Regenerate the manifest + reconcile Status headers. Returns flip list."""
    records = ps.read_ledger_all()
    links = ps.derive_links(records)
    ps.manifest_path().write_text(ps.build_manifest(records, links), encoding="utf-8")
    ps.upsert_work_projects(records, links)  # WORK.md `## Projects` surface (Option-1)
    flips = []
    for slug in ps.homes():
        derived = ps.derive_state(slug, records, links)
        if derived == "unknown":
            continue
        pm = ps.projects_root() / slug / "PROJECT.md"
        header = ps.parse_status_header(pm)
        if header is None:
            if ps.normalize_status_header(pm, derived):
                flips.append(f"{slug}: (legacy header) → {derived}")
        elif header != derived:
            if ps.sync_status_header(pm, derived):
                flips.append(f"{slug}: {header} → {derived}")
    return flips


def cmd_new(args) -> int:
# TA: xref: feature_041 (pause_2026-08-30d.md R6): lifecycle auto-sync hook — cmd_new/link/close/archive/reopen call net.state.lifecycle_sync_hook(event) via LAZY import in try/except (fail-open: net errors never block the lifecycle op; skip silently when the net bundle is unbootstrapped — bootstrap stays an explicit agent action per IDEA-002 §5.1); hook is proposal-only (D4) + ledger-audited; test_project_lifecycle.py must stay green (hook output to stdout is part of the contract — keep it one line).
    slug = args.slug or slugify(args.name)
    home = ps.projects_root() / slug
    if home.exists():
        print(f"error: {home} already exists", file=sys.stderr)
        return 2
    mapping = {"SLUG": slug, "TITLE": args.name.strip().title(), "DATE": date.today().isoformat()}
    home.mkdir(parents=True)
    (home / "PROJECT.md").write_text(_render("project.md", mapping), encoding="utf-8")
    (home / "CURRENT_STATE.md").write_text(_render("current_state.md", mapping), encoding="utf-8")
    ps.write_record({"kind": "project", "op": "create", "project": slug})
    _sync_all()
    print(f"✅ created project home .projects/meta/{slug}/ (state: draft)")
    print("Next: iterate freely (non-gated); spawn features with "
          f"new_feature.py \"<name>\" --type <tt> --project {slug}")
    return 0


def cmd_link(args) -> int:
    if not (ps.projects_root() / args.project).is_dir():
        print(f"error: unknown project home '{args.project}'", file=sys.stderr)
        return 2
    records = ps.read_ledger_all()
    existing = ps.derive_links(records).get(args.feature)
    if existing and existing["project"] == args.project:
        print(f"already linked: {args.feature} → {args.project} (no-op)")
        return 0
    ps.write_record({
        "kind": "project_link", "project": args.project,
        "feature": args.feature, "origin": args.origin,
    })
    _sync_all()
    print(f"✅ linked {args.feature} → {args.project} (origin: {args.origin})")
    return 0


def cmd_log(args) -> int:
    current = ps.projects_root() / args.slug / "CURRENT_STATE.md"
    if not current.exists():
        print(f"error: {current} missing", file=sys.stderr)
        return 2
    text = current.read_text(encoding="utf-8")
    today = date.today().isoformat()
    lines = text.split("\n")
    header_idx = next((i for i, ln in enumerate(lines) if ln.startswith(f"## {today}")), None)
    if header_idx is not None:
        # same-day merge: append the bullet at the END of today's block
        end = next((i for i in range(header_idx + 1, len(lines))
                    if lines[i].startswith("## ") or lines[i] == "---"), len(lines))
        insert_at = end
        while insert_at > header_idx + 1 and not lines[insert_at - 1].strip():
            insert_at -= 1
        lines.insert(insert_at, f"- {args.note}")
    else:
        block = [f"## {today} (auto — project.py log)", "", f"- {args.note}", "", "---"]
        div = next((i for i, ln in enumerate(lines) if ln == "---"), len(lines))
        lines[div + 1:div + 1] = [""] + block
    current.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ logged to {args.slug}/CURRENT_STATE.md")
    return 0


def cmd_status(args) -> int:
    records = ps.read_ledger_all()
    links = ps.derive_links(records)
    slugs = [args.slug] if args.slug else ps.homes()
    print("| project | state | features | created | last event |")
    print("|---|---|---|---|---|")
    for slug in slugs:
        events = ps.project_events(records, slug)
        state = ps.derive_state(slug, records, links)
        feats = sorted(f for f, l in links.items() if l["project"] == slug)
        created = events[0].get("ts", "—")[:10] if events else "—"
        last = events[-1].get("ts", "—")[:10] if events else "—"
        print(f"| {slug} | {state} | {', '.join(feats) or '—'} | {created} | {last} |")
    return 0


def cmd_close(args) -> int:
    records = ps.read_ledger_all()
    links = ps.derive_links(records)
    features = sorted(f for f, l in links.items() if l["project"] == args.slug)
    if not args.force:
        # terminal ships only (Testing/Done completes; legacy records w/o phase count)
        done = {r.get("feature") for r in records
                if r.get("kind") == "complete"
                and r.get("phase") in (None, "Testing", "Done")}
        open_feats = [f for f in features if f not in done]
        if open_feats:
            print(f"error: linked features without a complete record: {', '.join(open_feats)}"
                  " — finish them or --force", file=sys.stderr)
            return 3
    ps.write_record({"kind": "project", "op": "close", "project": args.slug})
    ps.sync_status_header(ps.projects_root() / args.slug / "PROJECT.md", "complete")
    _sync_all()
    print(f"✅ project {args.slug} closed (state: complete)")
    if args.archive:
        return cmd_archive(args)
    return 0


def cmd_archive(args) -> int:
    records = ps.read_ledger_all()
    links = ps.derive_links(records)
    if ps.derive_state(args.slug, records, links) != "complete":
        print(f"error: only a complete project can be archived (close first)", file=sys.stderr)
        return 2
    src = ps.projects_root() / args.slug
    dest = ps.projects_archive() / args.slug
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    ps.sync_status_header(dest / "PROJECT.md", "archived")
    ps.write_record({"kind": "project", "op": "archive", "project": args.slug,
                     "archived_to": f".projects/archive/{args.slug}"})
    _sync_all()
    print(f"✅ project {args.slug} archived → .projects/archive/{args.slug}/")
    return 0


def cmd_reopen(args) -> int:
    records = ps.read_ledger_all()
    links = ps.derive_links(records)
    state = ps.derive_state(args.slug, records, links)
    if state not in ("complete", "archived"):
        print(f"error: cannot reopen a project in state '{state}'", file=sys.stderr)
        return 2
    if state == "archived":
        src = ps.projects_archive() / args.slug
        if src.is_dir():
            shutil.move(str(src), str(ps.projects_root() / args.slug))
    ps.write_record({"kind": "project", "op": "reopen", "project": args.slug})
    _sync_all()
    print(f"✅ project {args.slug} reopened (state: "
          f"{ps.derive_state(args.slug, ps.read_ledger_all(), links)})")
    return 0


def cmd_sync(_args) -> int:
    flips = _sync_all()
    print(f"✅ manifest regenerated: {ps.manifest_path()}")
    for flip in flips:
        print(f"   header reconciled: {flip}")
    return 0


def cmd_backfill(args) -> int:
    """Adopt a pre-mechanic home: write the create record iff the slug has no
    lifecycle records yet (idempotent). Links use `link --origin backfill`."""
    if not (ps.projects_root() / args.slug).is_dir():
        print(f"error: unknown project home '{args.slug}'", file=sys.stderr)
        return 2
    records = ps.read_ledger_all()
    if ps.project_events(records, args.slug):
        print(f"backfill no-op: {args.slug} already has lifecycle records")
        return 0
    ps.write_record({"kind": "project", "op": "create", "project": args.slug,
                     "note": "backfill — home predates the mechanic"})
    _sync_all()
    print(f"✅ backfilled {args.slug} (create record written; origin:backfill links via "
          f"`project.py link <feature> {args.slug} --origin backfill`)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OMT++ project lifecycle CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new"); p.add_argument("name"); p.add_argument("--slug", default=None)
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser("link"); p.add_argument("feature"); p.add_argument("project")
    p.add_argument("--origin", default="manual", choices=sorted(ps.VALID_LINK_ORIGINS))
    p.set_defaults(fn=cmd_link)
    p = sub.add_parser("log"); p.add_argument("slug"); p.add_argument("note")
    p.set_defaults(fn=cmd_log)
    p = sub.add_parser("status"); p.add_argument("slug", nargs="?", default=None)
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("close"); p.add_argument("slug")
    p.add_argument("--force", action="store_true"); p.add_argument("--archive", action="store_true")
    p.set_defaults(fn=cmd_close)
    p = sub.add_parser("archive"); p.add_argument("slug"); p.set_defaults(fn=cmd_archive)
    p = sub.add_parser("reopen"); p.add_argument("slug"); p.set_defaults(fn=cmd_reopen)
    p = sub.add_parser("sync"); p.set_defaults(fn=cmd_sync)
    p = sub.add_parser("backfill"); p.add_argument("slug"); p.set_defaults(fn=cmd_backfill)
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
