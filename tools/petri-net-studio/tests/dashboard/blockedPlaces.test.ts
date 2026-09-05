// @vitest-environment node
/**
 * blockedPlaces vectors — feature_043 (operation_spec_001, pure DOM-free).
 *
 * For each disabled transition, its empty input places are reported (sorted,
 * deduped); `deadlocked` iff nothing is enabled.
 */

import { describe, expect, it } from "vitest";

import { blockedPlaces } from "../../src/dashboard/blockedPlaces.js";
import type { NetDocument } from "../../src/state/document.js";

const SINGLE: NetDocument = {
  places: [
    { name: "p_ready", tokens: 0 },
    { name: "p_done", tokens: 0 },
    { name: "cap", tokens: 0 },
  ],
  transitions: [{ name: "do_p" }, { name: "free_t" }],
  arcs: [
    { source: "p_ready", target: "do_p", weight: 1 },
    { source: "cap", target: "do_p", weight: 1 },
    { source: "do_p", target: "p_done", weight: 1 },
  ],
};

describe("blockedPlaces", () => {
  it("collects the empty inputs of a disabled transition", () => {
    const net = { ...SINGLE };
    // marking over placeOrder (code-point sorted): cap, p_done, p_ready
    const res = blockedPlaces(net, [1, 0, 0]);
    expect(res.blocked).toEqual(["p_ready"]);
    expect(res.deadlocked).toBe(false);
  });

  it("dedupes and sorts across transitions; all-enabled is clean", () => {
    const res = blockedPlaces(SINGLE, [1, 1, 0]);
    expect(res.blocked).toEqual(["p_ready"]);
    const open = blockedPlaces(SINGLE, [1, 0, 1]);
    expect(open.blocked).toEqual([]);
    expect(open.deadlocked).toBe(false);
  });

  it("empty net is deadlocked", () => {
    const res = blockedPlaces({ places: [], transitions: [], arcs: [] }, []);
    expect(res).toEqual({ blocked: [], deadlocked: true });
  });

  it("live-pool shape flags agent_attention for work_start", () => {
    const pool: NetDocument = {
      places: [
        { name: "agent_attention", tokens: 0 },
        { name: "feature_ready", tokens: 0 },
        { name: "work_active", tokens: 0 },
        { name: "work_pending", tokens: 0 },
      ],
      transitions: [{ name: "work_start" }, { name: "work_complete" }],
      arcs: [
        { source: "agent_attention", target: "work_start", weight: 1 },
        { source: "feature_ready", target: "work_start", weight: 1 },
        { source: "work_pending", target: "work_start", weight: 1 },
        { source: "work_start", target: "feature_ready", weight: 1 },
        { source: "work_start", target: "work_active", weight: 1 },
        { source: "work_active", target: "work_complete", weight: 1 },
      ],
    };
    // attention held by active work: agent_attention=0, work_active=1
    const res = blockedPlaces(pool, [0, 1, 1, 1]);
    expect(res.blocked).toEqual(["agent_attention"]);
    expect(res.deadlocked).toBe(false);
  });
});
