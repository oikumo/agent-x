"""Harness-owned Petri-net engine + state store (feature_039.adaptive_net_engine).

Meta-harness concurrency SSOT layer (meta_harness_concurrent, PROJECT.md
D1–D18): a parity clone of the shipped `src/agentx/model/petri_net/` library
(D2 — NO runtime import of `src/`), plus the three-file net-bundle store
(`state.py`) and the `omt_net` CLI (`cli.py`; ops probe|fire|invariant here,
splice|sync|synthesize reserved for feature_040+).

Parity is pinned by the 9 shared conformance vectors
(`shared/petri-net/conformance/analysis-v1/` →
`tests/scripts/omt/test_net_conformance.py`).
"""
