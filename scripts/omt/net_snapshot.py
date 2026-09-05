#!/usr/bin/env python3
"""Dashboard snapshot builder — thin shim (feature_043.meta_net_dashboard).

Regenerates the committed dashboard snapshot from the live harness bundle:

    uv run scripts/omt/net_snapshot.py [--out PATH]

Default out: tools/petri-net-studio/src/dashboard/snapshot.json (git-pinned,
like the conformance vectors). Refuses (exit 1) when the ledger replay does
not reproduce the live bundle exactly — regenerate after sync/fire, never
ship stale (fail-closed, D16).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from net.history import build_snapshot  # noqa: E402
from net.state import SpliceError, net_dir  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "tools" / "petri-net-studio" / "src" / "dashboard" / "snapshot.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="net_snapshot", description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)
    try:
        snapshot = build_snapshot(net_dir())
    except SpliceError as exc:
        print(json.dumps({"ok": False, "error": exc.code, "message": str(exc)}))
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "snapshot_revision": snapshot["net_revision"],
        "snapshots": len(snapshot["snapshots"]),
        "skipped": len(snapshot["skipped"]),
        "out": str(out),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
