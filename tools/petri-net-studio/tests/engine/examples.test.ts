// @vitest-environment node
/**
 * Shared examples as cross-implementation golden vectors (design_001 §9.2):
 * each example loads cleanly, its enabled set at M0 matches the Python
 * library's behavior (verified against io.py 2026-08-23), and the document
 * round-trips to the exact file bytes (D7 byte-identity contract).
 */

import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { documentFromJson, netToJson } from "../../src/engine/io.js";

const EXAMPLES = new URL("../../../../shared/petri-net/examples/", import.meta.url);

const CASES = [
  { name: "hello.json", enabledAtM0: ["t1"] },
  { name: "producer_consumer.json", enabledAtM0: ["produce"] },
  { name: "weighted_reaction.json", enabledAtM0: ["react"] },
] as const;

describe("TestSharedExamples", () => {
  it.each(CASES)("%s loads with expected enabled set and golden bytes", ({ name, enabledAtM0 }) => {
    const text = readFileSync(new URL(name, EXAMPLES), "utf-8");
    const doc = documentFromJson(text);
    expect(doc.net.enabledTransitionsAt(doc.net.currentMarking())).toEqual([...enabledAtM0]);
    expect(netToJson(doc.net, doc.layout)).toBe(text);
  });
});
