"""P0-2 dangling-active-only — feature_060.

Contract:
- omt_status lists ≤10 *unexpired* dangling (oldest-first) + expired GC count.
- Expired auto-hide (8h UNLOCK_WINDOW is the one-session grace); hidden
  records stay resumable via explicit re-declare / abandon tombstone.
- Header `Dangling phases: N (M expired)` unchanged (e2e shape pin).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
STATUS_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_status.ts"

BUN = shutil.which("bun")


def _run_probe(tmp_path: Path, body: str) -> dict:
    assert BUN is not None, "bun runtime required"
    probe = tmp_path / "probe.ts"
    probe.write_text(body, encoding="utf-8")
    env = {**os.environ, "OMT_LEDGER_PATH": str(tmp_path / "ledger.jsonl")}
    out = subprocess.run([BUN, str(probe)], capture_output=True, text=True,
                         timeout=90, cwd=str(tmp_path), env=env)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return json.loads(out.stdout.strip().splitlines()[-1])


PROBE = """import { writeFileSync } from "node:fs";
const LEDGER = process.env.OMT_LEDGER_PATH;
const H = 3600 * 1000, now = Date.now();
const iso = (ms) => new Date(ms).toISOString();
const recs = [];
for (let i = 0; i < 12; i++) {
  recs.push({ ts: iso(now - (30 + i) * 60 * 1000), kind: "phase", session: "p",
    task_type: "minor_feature", phase: "Programming", scope: "s", feature: `feature_A${String(i).padStart(2, "0")}.x` });
}
recs.push({ ts: iso(now - 9 * H), kind: "phase", session: "p",
  task_type: "minor_feature", phase: "Design", scope: "old", feature: "feature_OLD.x" });
writeFileSync(LEDGER, recs.map((r) => JSON.stringify(r)).join("\\n") + "\\n");
const plugin = await (await import("STATUS_ABS")).default({ directory: "TMP_ABS", worktree: "TMP_ABS" });
const res = await plugin.tool.omt_status.execute({}, {});
console.log(JSON.stringify({ output: res.output, hygiene: res.metadata.skip_hygiene }));
"""


class TestDanglingActiveOnly:
    def test_active_capped_gc_expired(self, tmp_path: Path) -> None:
        body = (PROBE.replace("STATUS_ABS", STATUS_PLUGIN.as_posix())
                .replace("TMP_ABS", tmp_path.as_posix()))
        out = _run_probe(tmp_path, body)
        h = out["hygiene"]
        assert h["dangling_total"] == 13, h
        assert h["dangling_expired"] == 1, h
        assert h["dangling_active"] == 12, h
        text = out["output"]
        assert "Dangling phases: 13 (1 expired)" in text
        # ≤10 active bullets (cap) + overflow line, oldest-first.
        bullets = [ln for ln in text.splitlines() if ln.strip().startswith("•")]
        assert len(bullets) == 10, bullets
        assert "2 more active (oldest shown)" in text
        assert "1 expired auto-hidden" in text
        assert "feature_OLD.x" not in text
        assert "resume: omt_phase{" in text and "abandon: omt_phase{" in text

    def test_no_dangling_no_gc_line(self, tmp_path: Path) -> None:
        body = """import { writeFileSync } from "node:fs";
const LEDGER = process.env.OMT_LEDGER_PATH;
writeFileSync(LEDGER, "");
const plugin = await (await import("STATUS_ABS")).default({ directory: "TMP_ABS", worktree: "TMP_ABS" });
const res = await plugin.tool.omt_status.execute({}, {});
console.log(JSON.stringify({ output: res.output, hygiene: res.metadata.skip_hygiene }));
""".replace("STATUS_ABS", STATUS_PLUGIN.as_posix()).replace("TMP_ABS", tmp_path.as_posix())
        out = _run_probe(tmp_path, body)
        assert out["hygiene"]["dangling_total"] == 0
        assert "Dangling phases: 0 (0 expired)" in out["output"]
        assert "auto-hidden" not in out["output"]
