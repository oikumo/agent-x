#!/usr/bin/env python3
"""TDD enforcement engine — compat shim (meta_harness_dsl R3).

The implementation moved into the scripts/omt/tdd/ package:
    tdd/state.py      ledger/snapshot/state IO + pytest runners + path resolution
    tdd/ast_checks.py AST analysis (import inference, true-RED, coverage gaps)
    tdd/gates.py      two-hats gate + after-edit advisory + validate-exit
    tdd/cli.py        cycle subcommands + argparse dispatch

This shim preserves every pre-split call site:
  - CLI:    uv run scripts/omt/tdd_check.py <subcommand> ...   (enforcer + docs)
  - Module: import tdd_check  → re-exports the full former public API
            (tests/scripts/omt/test_tdd_check.py imports it directly).
"""
from __future__ import annotations

import sys
from pathlib import Path

# The tdd package lives next to this shim (scripts/omt/tdd/). The script dir
# is already sys.path[0] when invoked as `uv run scripts/omt/tdd_check.py`;
# insert explicitly so `import tdd_check` works from any importer context.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tdd.ast_checks import (  # noqa: F401
    detect_red_anti_patterns,
    extract_defined_names,
    extract_public_methods,
    extract_test_references,
    extract_test_summary,
    find_untested_methods,
    infer_target_src,
    verify_true_red,
)
from tdd.gates import (  # noqa: F401
    HAT_RULES,
    cmd_after_edit,
    cmd_gate,
    cmd_validate_exit,
)
from tdd.state import (  # noqa: F401
    LEDGER_PATH,
    REPO_ROOT,
    SNAPSHOT_DIR,
    UNLOCK_WINDOW_MS,
    diff_snapshots,
    get_current_test_node,
    get_session_records,
    get_tdd_cycles,
    get_tdd_mode,
    get_tdd_state,
    load_snapshot,
    read_ledger,
    run_full_suite,
    run_pytest,
    snapshot_source,
    write_ledger,
)
from tdd.cli import (  # noqa: F401
    cmd_done,
    cmd_green,
    cmd_refactor,
    cmd_start,
    cmd_status,
    cmd_testlist,
    main,
)

if __name__ == "__main__":
    sys.exit(main())
