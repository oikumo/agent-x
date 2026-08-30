#!/usr/bin/env python3
"""omt_net CLI — compat shim (feature_039.adaptive_net_engine).

The implementation lives in the scripts/omt/net/ package:
    net/errors.py       PetriNetError hierarchy
    net/model.py        PetriNet (parity clone, D2 — no src/ import)
    net/analysis.py     PetriNetAnalyzer (parity clone)
    net/io.py           petri-net-json v1 load/save
    net/conformance.py  shared-vector runner (9 vectors, analysis-v1)
    net/state.py        three-file net-bundle store (sidecar/overlay, D6/D11)
    net/cli.py          omt_net ops probe|fire|invariant (IDEA-002 v4 §5.0)

Call site:
  - CLI: uv run scripts/omt/net_check.py probe|fire|invariant ...
         (the .opencode/plugins/omt_net.ts proxy invokes this shim).
"""
from __future__ import annotations

import sys
from pathlib import Path

# The net package lives next to this shim (scripts/omt/net/). The script dir
# is already sys.path[0] when invoked as `uv run scripts/omt/net_check.py`;
# insert explicitly so `import net_check` works from any importer context.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from net.cli import main  # noqa: F401

if __name__ == "__main__":
    sys.exit(main())
