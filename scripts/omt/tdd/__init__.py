"""TDD enforcement package (meta_harness_dsl R3).

Split of the former monolithic scripts/omt/tdd_check.py (825 lines):

  state.py      ledger/snapshot/state IO + pytest runners + path resolution
  ast_checks.py AST analysis (import inference, true-RED, coverage gaps)
  gates.py      two-hats gate + after-edit advisory + validate-exit
  cli.py        cycle subcommands + argparse dispatch

scripts/omt/tdd_check.py remains as a thin compat shim — the enforcer and
docs keep calling `tdd_check.py <subcommand>`; no call-site changes.
"""
