#!/usr/bin/env python3
"""OMT++ feature scaffolder.

Creates a new `feature_00N.<slug>/` under the requirements features directory with a
consistent FEATURE.md + plan/PLAN.md generated from `.meta/templates/`, enforcing the
naming convention so ad-hoc artifact sprawl (e.g. the 8 `TUI_*` files) cannot recur.

Usage:
    uv run scripts/omt/new_feature.py "modern ui"          # -> feature_007.modern_ui
    uv run scripts/omt/new_feature.py "modern ui" --type major_feature
    uv run scripts/omt/new_feature.py "modern ui" --dry-run

The plugin gate (.opencode/plugins/omt_enforcer.ts) calls this automatically for
feature-sized tasks so the design/analysis artifacts exist before src/ edits unlock.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO_ROOT / ".meta" / "software_development_process" / "2.requirements" / "features"
TEMPLATES_DIR = REPO_ROOT / ".meta" / "templates"

VALID_TYPES = {"bug_fix", "minor_feature", "major_feature", "new_screen", "refactor"}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    if not slug:
        raise SystemExit("error: feature name produces an empty slug")
    return slug


def next_feature_number() -> int:
    highest = 0
    if FEATURES_DIR.is_dir():
        for child in FEATURES_DIR.iterdir():
            m = re.match(r"feature_(\d+)\.", child.name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest + 1


def render(template_name: str, mapping: dict[str, str]) -> str:
    text = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
    for key, val in mapping.items():
        text = text.replace("{{" + key + "}}", val)
    return text


def build_plan_stub(num_str: str, title: str, slug: str, ttype: str) -> str:
    return (
        f"# PLAN — feature_{num_str}: {title}\n\n"
        f"> Task type: **{ttype}** · See `omt_agent_guide.md §12` for the required artifacts.\n\n"
        "## Objective\n\n<!-- one sentence: what done looks like -->\n\n"
        "## Steps\n\n- [ ] Analysis\n- [ ] Design\n- [ ] Implementation\n- [ ] Testing\n\n"
        "## Artifacts produced\n\n"
        f"- Requirements: `{slug}/FEATURE.md`\n"
        f"- Analysis: `3.analysis/features/{slug}/analysis_001_*.md`\n"
        f"- Design: `4.design/features/{slug}/design_001_*.md`\n"
        f"- Testing: `6.testing/features/{slug}/test_report.md`\n"
    )


def main(argv: list[str] | None = None) -> int:
# TA: xref: feature_041 (pause_2026-08-30d.md R6): --project link path triggers the same net.state.lifecycle_sync_hook("new_feature_link") as project.py lifecycle ops — lazy import + try/except fail-open, skip when unbootstrapped, proposal-only D4; wire AFTER the link ledger append so the resync scan already sees the new feature dir.
    parser = argparse.ArgumentParser(description="Scaffold a new OMT++ feature")
    parser.add_argument("name", help="human-readable feature name, e.g. 'modern ui'")
    parser.add_argument("--type", default="minor_feature", choices=sorted(VALID_TYPES))
    parser.add_argument("--date", default=None, help="ISO date stamp (default: today)")
    parser.add_argument("--project", default=None,
                        help="link the new feature to a .projects/meta/<slug> home "
                             "(spawn-time link, origin: scaffold — feature_030)")
    parser.add_argument("--dry-run", action="store_true", help="print what would be created")
    args = parser.parse_args(argv)

    if not TEMPLATES_DIR.is_dir():
        print(f"error: templates dir missing: {TEMPLATES_DIR}", file=sys.stderr)
        return 2

    slug = slugify(args.name)
    num = next_feature_number()
    num_str = f"{num:03d}"
    title = args.name.strip().title()
    date = args.date or _dt.date.today().isoformat()
    feature_slug = f"feature_{num_str}.{slug}"
    feature_dir = FEATURES_DIR / feature_slug

    mapping = {"NUM": num_str, "TITLE": title, "SLUG": feature_slug, "DATE": date}
    feature_md = render("feature.md", mapping)
    plan_md = build_plan_stub(num_str, title, feature_slug, args.type)

    targets = {
        feature_dir / "FEATURE.md": feature_md,
        feature_dir / "plan" / "PLAN.md": plan_md,
    }

    if feature_dir.exists():
        print(f"error: {feature_dir} already exists", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"[dry-run] would create {feature_slug}/ (type={args.type}):")
        for path in targets:
            print(f"  - {path.relative_to(REPO_ROOT)}")
        if args.project:
            print(f"  - would link {feature_slug} → {args.project} (origin: scaffold)")
        return 0

    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    print(f"✅ created {feature_slug}/")
    for path in targets:
        try:
            shown: Path | str = path.relative_to(REPO_ROOT)
        except ValueError:  # hermetic tests: FEATURES_DIR outside the repo
            shown = path
        print(f"   {shown}")
    if args.project:
        import project as project_cli
        rc = project_cli.main(["link", feature_slug, args.project, "--origin", "scaffold"])
        if rc != 0:
            print(f"⚠️ project link to '{args.project}' failed (rc={rc}) — run: "
                  f"uv run scripts/omt/project.py link {feature_slug} {args.project} --origin scaffold")
        else:
            # feature_041 R6: net lifecycle auto-sync AFTER the link ledger
            # append — lazy import + fail-open, proposal-only (D4).
            try:
                from net import state as net_state  # noqa: PLC0415

                net_state.lifecycle_sync_hook("new_feature_link")
            except Exception:  # noqa: BLE001 — fail-open by design (R6)
                pass
    print(f"\nNext: declare your phase before editing src/  →  omt_phase{{task_type:'{args.type}'}}")
    print("Naming: analysis_NNN_<topic>.md, design_NNN_<topic>.md (no ad-hoc *_PROOF.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
