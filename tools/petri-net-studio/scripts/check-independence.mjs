#!/usr/bin/env node
/**
 * Independence check (design_001 §8, project D4/D5).
 *
 * tools/petri-net-studio must be runtime-independent of agentx and the meta
 * harness — the ONLY coupling is the shared format data, which enters via
 * `?raw` imports in src/examples.ts (examples + conformance-vector fixture
 * nets — C7). This script walks src/ recursively (.ts/.tsx), scans
 * static/dynamic/side-effect import specifiers, and FAILS (exit 1) when a
 * specifier:
 *   - matches BANNED (agentx / scripts/ / .meta/ / .projects/ / tests/), or
 *   - is relative AND resolves outside src/ — except specifiers containing an
 *     allowlisted substring (`shared/petri-net/examples/` or
 *     `shared/petri-net/conformance/` — the ?raw coupling).
 *
 * Wired as `npm run check-independence`; also asserted by tests/independence.test.ts.
 */

import { readdirSync, readFileSync } from "node:fs";
import { dirname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = fileURLToPath(new URL("../src", import.meta.url));
const BANNED = /agentx|scripts\/|\.meta\/|\.projects\/|tests\//;
const ALLOWED_OUTSIDE = /shared\/petri-net\/(examples|conformance)\//;

const IMPORT_RE =
  /(?:import|export)\s[^'"]*?\sfrom\s*["']([^"']+)["']|import\s*\(\s*["']([^"']+)["']\s*\)|import\s*["']([^"']+)["']/g;

/** Recursively collect .ts/.tsx files under dir. */
function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = resolve(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(path));
    else if (/\.tsx?$/.test(entry.name)) out.push(path);
  }
  return out;
}

function* specifiersOf(file) {
  const text = readFileSync(file, "utf8");
  for (const match of text.matchAll(IMPORT_RE)) {
    const spec = match[1] ?? match[2] ?? match[3];
    if (spec !== undefined) yield spec;
  }
}

const offenses = [];
let files = 0;
let imports = 0;

for (const file of walk(SRC)) {
  files++;
  for (const spec of specifiersOf(file)) {
    imports++;
    if (ALLOWED_OUTSIDE.test(spec)) continue; // allowlisted ?raw shared-data coupling
    if (BANNED.test(spec)) {
      offenses.push(`${file}: banned specifier "${spec}"`);
      continue;
    }
    if (spec.startsWith(".")) {
      const resolved = resolve(dirname(file), spec.split("?")[0]);
      if (resolved !== SRC && !resolved.startsWith(SRC + sep)) {
        offenses.push(`${file}: relative import escapes src/: "${spec}"`);
      }
    }
  }
}

if (offenses.length > 0) {
  console.error(`independence FAILED — ${offenses.length} offending import(s):`);
  for (const o of offenses) console.error(`  ${o}`);
  process.exit(1);
}

console.log(`independence OK: ${files} files scanned, ${imports} imports checked`);
// TA: gotcha: gotcha: a glob like src/**/*.ts inside a JS block comment terminates it early (the **/ closes the comment) → SyntaxError at module load; first run of this script failed exactly so — write "walks src/ recursively" instead.
