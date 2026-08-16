#!/usr/bin/env python3
"""Golden tests for T1: omt_q{op:state} summary projection + verbose flag
(feature_028, meta_harness_3 v1.2 — user-approved shape 2026-08-16).

Measured driver (opencode.db + live probe): op=state averaged 29KB/call
(24–36KB range; 44KB live on this repo — risky_thoughts 31.6KB, recent_consults
5.9KB, decree_health 5.2KB). The default envelope becomes a summary (counts +
top-N, truncated payloads, ≤ ~2KB); verbose:true restores the byte-identical
full dump (the pre-T1 shape — the existing U8/U13 goldens migrate to
verbose:true and keep their assertions unchanged, pinning byte-identity).

Probe convention: bun probes against the real plugin source (test_omt_q.py
pattern), hermetic tmp root + fixture ledger + planted thoughts index.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
OMT_Q_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_q.ts"
SHARED_LIB = REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts"

BUN = shutil.which("bun")

_probe_template = """
import { initOmtShared } from "%LIB%"
initOmtShared(process.argv[2])
const mod = await import("%PLUGIN%")
const { tool } = await mod.default({ directory: process.argv[2], worktree: process.argv[2] })
const result = await tool.omt_q.execute(%ARGS%, { sessionID: "ses_t1" })
console.log(result)
"""


def _probe(args_str: str, tmp_path: Path) -> dict:
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    probe = tmp_path / "probe_t1.ts"
    probe.write_text(
        _probe_template.replace("%LIB%", str(SHARED_LIB))
        .replace("%PLUGIN%", str(OMT_Q_PLUGIN)).replace("%ARGS%", args_str),
        encoding="utf-8")
    out = subprocess.run([BUN, str(probe), str(tmp_path)],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return json.loads(out.stdout.strip().splitlines()[-1])


def _now_iso() -> str:
    """Dynamic timestamp inside the 8h consult window (no absolute dates —
    the feature_027 date-drift lesson)."""
    return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


@pytest.fixture()
def wide_root(tmp_path):
    """Hermetic root with a WIDE substrate: 25 slug variants, 12 empty-slug
    records with 300-char scopes, 4 invalid phases, 2 consult records with
    10 files each, 10 long thoughts — the T1 size drivers, hermetically."""
    omt = tmp_path / ".meta" / ".omt"
    omt.mkdir(parents=True)
    records = []
    for i in range(1, 26):
        records.append({"kind": "phase", "session": f"ses_{i:02d}",
                        "feature": f"feature_{i:03d}.slug_{i}",
                        "phase": "Programming", "ts": "2026-08-10T10:00:00+00:00"})
    for i in range(12):
        records.append({"kind": "phase", "session": f"ses_empty_{i}",
                        "feature": "", "phase": "Analysis",
                        "scope": f"scope-sentence-{i} " + "x" * 280,
                        "ts": "2026-08-11T10:00:00+00:00"})
    for i in range(4):
        records.append({"kind": "phase", "session": f"ses_bad_{i}",
                        "feature": "feature_001.slug_1", "phase": "Hacking",
                        "ts": "2026-08-12T10:00:00+00:00"})
    for i in range(2):
        records.append({"kind": "think_consult", "session": "ses_t1",
                        "files": [f"src/agentx/mod_{j}/file_{j}.py" for j in range(10)],
                        "ts": _now_iso()})
    with open(omt / "ledger.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    with open(omt / "thoughts.jsonl", "w", encoding="utf-8") as f:
        for i in range(10):
            f.write(json.dumps({
                "category": "gotcha", "path": f"src/agentx/deep/module_{i}.py",
                "line": 10 + i, "ts": "2026-08-13T10:00:00+00:00",
                "thought": f"thought-{i} " + "y" * 380,
            }) + "\n")
    return tmp_path


class TestStateSummaryProjection:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_default_state_envelope_is_compact_summary(self, wide_root):
        """T1: the default op=state envelope is counts + top-N with truncated
        payloads — ≤ 2KB on a substrate that produced ~10KB pre-T1."""
        out = _probe('{"op":"state"}', wide_root)
        size = len(json.dumps(out))
        assert size <= 2048, f"default envelope {size}B exceeds the 2KB T1 budget"
        dh = out["decree_health"]
        assert dh["slug_variants_count"] == 25
        assert dh["empty_slug_count"] == 12
        assert dh["invalid_phase_count"] == 4
        assert len(dh["slug_variants_sample"]) <= 3
        assert len(dh["empty_slug_sample"]) <= 3
        assert all(len(r["scope"]) <= 81 for r in dh["empty_slug_sample"])
        assert out["risky_thoughts"]["count"] == 10
        assert len(out["risky_thoughts"]["top"]) <= 3
        assert out["recent_consults"]["count"] == 2

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_verbose_restores_byte_identical_full_dump(self, wide_root):
        """T1: verbose:true restores the pre-T1 full shape — every payload
        complete and untruncated (the U8/U13 golden shapes)."""
        full = _probe('{"op":"state","verbose":true}', wide_root)
        compact = _probe('{"op":"state"}', wide_root)
        dh = full["decree_health"]
        assert len(dh["slug_variants"]) == 25
        assert len(dh["empty_slug_records"]) == 12
        assert any(len(r["scope"]) >= 280 for r in dh["empty_slug_records"])
        assert len(dh["invalid_phase_records"]) == 4
        assert isinstance(full["recent_consults"], list)
        assert len(full["recent_consults"]) == 2
        assert len(full["recent_consults"][0]["files"]) == 10
        assert isinstance(full["risky_thoughts"], list)
        assert len(full["risky_thoughts"]) == 10
        assert any(len(t["thought"]) >= 380 for t in full["risky_thoughts"])
        assert len(json.dumps(full)) > len(json.dumps(compact))
