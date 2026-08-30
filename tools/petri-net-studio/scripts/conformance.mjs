#!/usr/bin/env node
/**
 * Conformance runner (design_001 §7; feature_036 Cycle 6, C8).
 *
 * Wired as `npm run conformance`. Sequential side-effect script, exit 0 ONLY
 * if all three steps pass:
 *
 *   1. regenerate vectors — `uv run python scripts/generate-vectors.py` (cwd =
 *      studio). Uses the TESTED Python library as the executable spec.
 *   2. assert `git status --porcelain shared/petri-net/conformance/` is EMPTY —
 *      the generator's determinism contract: a re-run must be byte-identical
 *      (canonical member order, sorted arrays; fail otherwise with a diff hint).
 *   3. run the existing Vitest conformance suite —
 *      `npx vitest run tests/engine/conformance.test.ts`.
 *
 * Prints a step-by-step summary. Non-zero exit + message on any failure.
 *
 * Disposition (C8): the Vitest runner itself shipped in feature_035; this
 * script is the roadmap #5 "runner wiring" formality + the extension path for
 * the vector corpus (drop new fixture ids in generate-vectors.py → re-run).
 */

import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const STUDIO = fileURLToPath(new URL("..", import.meta.url));
const REPO_ROOT = fileURLToPath(new URL("../../..", import.meta.url));

function run(step, label, cmd, args, opts = {}) {
  process.stdout.write(`\n[${step}] ${label}\n  $ ${cmd} ${args.join(" ")}\n`);
  const res = spawnSync(cmd, args, { cwd: opts.cwd ?? STUDIO, stdio: "inherit" });
  if (res.error) {
    process.stderr.write(`\n[${step}] FAILED to spawn: ${res.error.message}\n`);
    process.exit(1);
  }
  return res.status;
}

let failed = false;

// Step 1 — regenerate vectors (Python library as executable spec).
const s1 = run(1, "Regenerate conformance vectors", "uv", [
  "run",
  "python",
  "scripts/generate-vectors.py",
]);
if (s1 !== 0) {
  process.stderr.write(`[1] FAILED — generator exited ${s1}\n`);
  failed = true;
}

// Step 2 — byte-identical determinism check (git status must be EMPTY).
if (!failed) {
  const check = spawnSync(
    "git",
    ["status", "--porcelain", "shared/petri-net/conformance/"],
    { cwd: REPO_ROOT, encoding: "utf8" },
  );
  const dirty = (check.stdout ?? "").trim();
  process.stdout.write(
    `[2] Byte-identical determinism check (git status --porcelain shared/petri-net/conformance/)\n` +
      `    → ${dirty === "" ? "CLEAN (re-run byte-identical)" : "DIRTY"}\n`,
  );
  if (check.status !== 0 || dirty !== "") {
    process.stderr.write(
      `[2] FAILED — generator is not deterministic: ${dirty.split("\n").join(" | ")}\n` +
        `    Hint: git diff shared/petri-net/conformance/ — vector bytes changed on re-run.\n`,
    );
    failed = true;
  }
}

// Step 3 — existing Vitest conformance suite.
if (!failed) {
  const s3 = run(3, "Run Vitest conformance suite", "npx", [
    "vitest",
    "run",
    "tests/engine/conformance.test.ts",
  ]);
  if (s3 !== 0) {
    process.stderr.write(`[3] FAILED — vitest exited ${s3}\n`);
    failed = true;
  }
}

if (failed) {
  process.stderr.write(`\nconformance: FAILED\n`);
  process.exit(1);
}
process.stdout.write(`\nconformance: all 3 steps OK\n`);