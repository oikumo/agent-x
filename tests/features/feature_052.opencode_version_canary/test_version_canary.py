"""Wave 1/F1 opencode_version_canary (feature_052): fail-loud canary for
live-binary drift.

The harness gates were audited against ONE opencode line (.omt @var
opencode_version_range → ir.vars). An opencode upgrade can silently change
SDK/plugin behavior — the F14 lesson: a gate that stops firing without
notice is worse than no gate. This suite fails LOUDLY the moment
`opencode --version` leaves the audited range. Re-baselining is then a
deliberate act: run the live smoke (test_omt_live_opencode_guards.py) +
full suite on the new binary, bump the @var, `harnessc build`, done.

The comparator grammar is shared with the TS runtime
(.opencode/lib/enforcer/nav_gate.ts versionInRange — exercised against the
REAL implementation by the R6 bun probes, see implementation_notes.md):
comma-separated comparators, each `>=V | <=V | >V | <V | =V | V(exact)`
with V dotted-numeric; ALL must hold. Unparsable version/range = no-signal
(the plugin fails open; THIS suite fails — a test that cannot parse its
own range is broken, not quiet).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
IR = REPO_ROOT / ".meta" / ".omt" / "harness.ir.json"
NAV_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "nav_gate.ts"

OPENCODE = shutil.which("opencode")

_OP_RE = re.compile(r"^(>=|<=|>|<|=)?(\d+(?:\.\d+)*)$")


def _parse_dotted(s: str) -> tuple[int, ...] | None:
    s = s.strip()
    if not re.fullmatch(r"\d+(?:\.\d+)*", s):
        return None
    return tuple(int(p) for p in s.split("."))


def _cmp(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    n = max(len(a), len(b))
    a = a + (0,) * (n - len(a))
    b = b + (0,) * (n - len(b))
    return (a > b) - (a < b)


def in_range(ver: str, range: str) -> bool | None:
    """Python mirror of nav_gate.ts versionInRange (grammar pin below)."""
    v = _parse_dotted(ver)
    if v is None:
        return None
    parts = [p.strip() for p in range.split(",") if p.strip()]
    if not parts:
        return None
    for p in parts:
        m = _OP_RE.match(p)
        if not m:
            return None
        bound = tuple(int(x) for x in m.group(2).split("."))
        c = _cmp(v, bound)
        op = m.group(1) or "="
        ok = (c == 0 if op == "=" else c >= 0 if op == ">="
              else c <= 0 if op == "<=" else c > 0 if op == ">" else c < 0)
        if not ok:
            return False
    return True


def _ir() -> dict:
    return json.loads(IR.read_text(encoding="utf-8"))


def _ir_range() -> str:
    rng = _ir()["vars"]["opencode_version_range"]
    assert isinstance(rng, str) and rng, (
        "IR vars.opencode_version_range missing/empty — .omt @var "
        "opencode_version_range + `harnessc build` required")
    return rng


def _live_version() -> str:
    proc = subprocess.run(
        ["opencode", "--version"], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, f"opencode --version failed: {proc.stderr[-300:]!r}"
    ver = proc.stdout.strip().split()[0]
    assert _parse_dotted(ver) is not None, (
        f"unparsable `opencode --version` output: {proc.stdout.strip()!r}")
    return ver


class TestRangeVar:
    def test_range_present_and_parses(self):
        rng = _ir_range()
        assert in_range("0.0.0", rng) is not None, (
            f"audited range does not parse per the canary grammar: {rng!r}")

    def test_msg_wired_with_baked_range(self):
        """@msg wrn_opencode_version exists, range baked at build (OPT-C),
        no unresolved {@var.} remnant, and the TS runtime consumes it."""
        msgs = _ir()["msgs"]
        assert "wrn_opencode_version" in msgs, (
            "IR msgs.wrn_opencode_version missing — .omt @msg + build required")
        text = msgs["wrn_opencode_version"]["text"]
        assert "{@var." not in text, (
            f"uninterpolated var ref in compiled msg text: {text!r}")
        assert _ir_range() in text, (
            "compiled msg must carry the baked audited range "
            f"({_ir_range()!r} not in {text!r})")
        src = NAV_GATE.read_text(encoding="utf-8")
        assert 'gateMsg("wrn_opencode_version"' in src, (
            "orphan-msg guard: no TS gateMsg(\"wrn_opencode_version\") "
            "consumer in nav_gate.ts (harnessc check_msg_orphans enforces this)")


class TestRangeGrammar:
    @pytest.mark.parametrize("ver,rng,want", [
        ("1.18.29", ">=1.18.29,<1.19", True),    # audited floor, live today
        ("1.18.5", ">=1.18.29,<1.19", False),    # below floor
        ("1.19.0", ">=1.18.29,<1.19", False),    # next minor line
        ("1.18.29", "1.18.29", True),            # exact pin
        ("1.18.30", "1.18.29", False),
        ("2.0", ">1.0,<=2.0", True),
        ("2.0.1", ">1.0,<=2.0", False),
        ("1.18.29", ">=1.18", True),             # short bound pads with 0
        ("1.18", ">=1.18.29", False),
    ])
    def test_comparator_matrix(self, ver: str, rng: str, want: bool):
        assert in_range(ver, rng) is want

    @pytest.mark.parametrize("ver,rng", [
        ("abc", ">=1.0"),          # unparsable version
        ("1.0", ">=abc"),          # unparsable bound
        ("1.0", ""),               # empty range
        ("1.0", ">>1.0"),          # bad operator
        ("", ">=1.0"),
    ])
    def test_unparsable_is_no_signal(self, ver: str, rng: str):
        assert in_range(ver, rng) is None


@pytest.mark.skipif(not OPENCODE, reason="opencode binary not available")
class TestLiveBinaryCanary:
    def test_live_binary_inside_audited_range(self):
        """THE canary: fails loudly on opencode upgrade until deliberate
        re-baseline (live smoke + full suite on the new binary, bump @var)."""
        rng = _ir_range()
        ver = _live_version()
        assert in_range(ver, rng) is True, (
            f"OPENCODE DRIFT: live binary {ver} left the audited range {rng} — "
            "gates were audited against that line. Re-baseline deliberately: "
            "live smoke + full suite on the new binary, bump .omt @var "
            "opencode_version_range, rebuild.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
