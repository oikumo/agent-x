#!/usr/bin/env python3
"""Pin tests for feature_046.omt_net_session_arg_whitelist (bug_fix).

The omt_net.ts proxy must build argv from a PER-OP whitelist that mirrors the
CLI subparser declarations in scripts/omt/net/cli.py. Pre-fix it appended
--session (context.sessionID fallback) to EVERY op's argv, but the probe /
invariant / synthesize subparsers declare no --session → argparse exit 2
'unrecognized arguments' → omt_net{op:probe|invariant} via the plugin ALWAYS
failed (latent since feature_039; surfaced by the feature_041 R4 dogfood —
TA gotcha @ omt_net.ts:43).

Pin discipline: cross-source — the plugin whitelist is parsed out of the .ts
and checked SUBSET of the flags the matching cli.py subparser declares, so
the test fails whenever proxy and CLI drift apart in either direction.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_PY = REPO_ROOT / "scripts" / "omt" / "net" / "cli.py"
PLUGIN_TS = REPO_ROOT / ".opencode" / "plugins" / "omt_net.ts"

# Plugin-only arg handled outside the whitelist loop (probe's --max-states).
EXTRA_ALLOWED = {"probe": {"max_states"}}


def _cli_flags_by_op() -> dict[str, set[str]]:
    """Parse cli.py: subparser name -> declared --flags (normalized: no dashes,
    '-'->'_' so '--max-states' -> 'max_states'). Multi-line tolerant: slices the
    source between consecutive add_parser name matches (black wraps long calls,
    e.g. splice's add_parser/add_argument span multiple lines)."""
    src = CLI_PY.read_text(encoding="utf-8")
    flags: dict[str, set[str]] = {}
    marks = [(m.group(1), m.start()) for m in re.finditer(r'add_parser\(\s*"(\w+)"', src)]
    for i, (name, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(src)
        flags[name] = {
            a[2:].replace("-", "_")
            for a in re.findall(r'add_argument\(\s*"(--[\w-]+)"', src[start:end])
        }
    return flags


def _plugin_whitelist() -> dict[str, list[str]]:
    """Parse omt_net.ts OP_ARGS: op -> whitelisted arg keys."""
    src = PLUGIN_TS.read_text(encoding="utf-8")
    m = re.search(r"OP_ARGS\s*:[^=]*=\s*\{(.*?)\n\s*\}", src, re.S)
    assert m, "omt_net.ts must declare a per-op OP_ARGS whitelist (feature_046)"
    out: dict[str, list[str]] = {}
    for op, body in re.findall(r'(\w+):\s*\[([^\]]*)\]', m.group(1)):
        out[op] = re.findall(r'"(\w+)"', body)
    return out


def _plugin_ops() -> list[str]:
    src = PLUGIN_TS.read_text(encoding="utf-8")
    m = re.search(r"const OPS = \[(.*?)\]", src)
    assert m
    return re.findall(r'"(\w+)"', m.group(1))


class TestPerOpWhitelistExists:
    def test_every_op_has_a_whitelist_entry(self):
        wl = _plugin_whitelist()
        for op in _plugin_ops():
            assert op in wl, f"OP_ARGS missing entry for op {op!r}"

    def test_argv_loop_iterates_the_per_op_whitelist(self):
        """The session fallback must live inside a loop over OP_ARGS[op] —
        a revert to one fixed arg list for all ops re-opens the bug."""
        src = PLUGIN_TS.read_text(encoding="utf-8")
        assert re.search(r"for \(const k of OP_ARGS\[op\]\)", src), (
            "argv construction must iterate OP_ARGS[op], not a fixed list"
        )
        assert "context?.sessionID" in src  # fallback retained, but scoped

    def test_max_states_is_scoped_to_probe(self):
        """--max-states exists only on the probe subparser (the one
        whitelist-exempt arg) — it must be gated on op === "probe"; appending
        it unconditionally is the same bug class as the --session defect."""
        src = PLUGIN_TS.read_text(encoding="utf-8")
        assert re.search(r'if \(op === "probe"[^\n]*max_states[^\n]*\)', src), (
            "the max_states push must be guarded by op === \"probe\""
        )


class TestWhitelistMirrorsCli:
    def test_whitelisted_args_are_subset_of_cli_flags(self):
        cli = _cli_flags_by_op()
        for op, args in _plugin_whitelist().items():
            allowed = cli.get(op, set()) | EXTRA_ALLOWED.get(op, set())
            extras = set(args) - allowed
            assert not extras, (
                f"op {op!r}: proxy sends {sorted(extras)} but the CLI subparser "
                f"declares only {sorted(cli.get(op, set()))}"
            )

    def test_probe_invariant_synthesize_get_no_session(self):
        """The concrete regression: probe/invariant (and reserved synthesize)
        must never receive --session — their subparsers reject it."""
        wl = _plugin_whitelist()
        for op in ("probe", "invariant", "synthesize"):
            assert "session" not in wl.get(op, []), op

    def test_session_accepting_ops_keep_session(self):
        """fire/splice/sync DO declare --session — the whitelist must not
        over-trim (their audit records key on it)."""
        wl = _plugin_whitelist()
        for op in ("fire", "splice", "sync"):
            assert "session" in wl.get(op, []), op
