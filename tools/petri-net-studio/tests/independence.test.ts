// @vitest-environment node
/**
 * Independence lint as a test (design §8): spawn scripts/check-independence.mjs
 * so a plain `npm test` covers the no-agentx/harness-imports rule (project D4).
 * Node env required: uses child_process + import.meta.url (jsdom rewrites it).
 */

import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

describe("TestIndependence", () => {
  it("src/ has no agentx/harness imports (scripts/check-independence.mjs)", () => {
    const cwd = fileURLToPath(new URL("..", import.meta.url));
    const out = execFileSync(process.execPath, ["scripts/check-independence.mjs"], {
      cwd,
      encoding: "utf8",
    });
    expect(out).toMatch(/independence OK/);
  });
});
// TA: gotcha: gotcha: node env required — jsdom rewrites import.meta.url to http://… (breaks cwd resolution) and child_process must be real; same class as the io.test.ts engine docblock pin.
