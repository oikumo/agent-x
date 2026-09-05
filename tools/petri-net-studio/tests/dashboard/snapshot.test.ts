// @vitest-environment node
/**
 * Committed snapshot guard — feature_043 (operation_spec_001 §2 contract).
 *
 * The dashboard snapshot is generated + committed (git-pinned like the
 * conformance vectors); regen = `uv run scripts/omt/net_snapshot.py`.
 * Staleness is banner-visible at runtime, but shape violations fail here.
 */

import { describe, expect, it } from "vitest";

import snapshot from "../../src/dashboard/snapshot.json";

interface SnapshotFile {
  format: string;
  version: number;
  net_revision: number;
  place_order: string[];
  net: { places: { name: string }[]; transitions: { name: string }[]; arcs: unknown[] };
  positions: Record<string, { x: number; y: number }>;
  pool: { pending: number; active: number; done: number };
  snapshots: { revision: number; kind: string; label: string; marking: Record<string, number> }[];
}

const snap = snapshot as unknown as SnapshotFile;

describe("dashboard snapshot", () => {
  it("is version 1 of the dashboard snapshot format", () => {
    expect(snap.format).toBe("meta-net-dashboard-snapshot");
    expect(snap.version).toBe(1);
  });

  it("final marking covers the place order exactly; revisions increase", () => {
    // Early snapshots may name long-removed places (structural history);
    // per-revision structural fidelity is proven by the pytest live golden
    // (exact marking equality). Here: the live snapshot matches place_order.
    const order = new Set(snap.place_order);
    expect(order.size).toBeGreaterThan(0);
    const last = snap.snapshots[snap.snapshots.length - 1];
    expect(new Set(Object.keys(last.marking))).toEqual(order);
    for (const s of snap.snapshots) {
      expect(Object.keys(s.marking).length).toBeGreaterThan(0);
    }
    const revs = snap.snapshots.map((s) => s.revision);
    expect([...revs].sort((a, b) => a - b)).toEqual(revs);
    expect(revs[revs.length - 1]).toBe(snap.net_revision);
  });

  it("net shape and positions cover every node", () => {
    const names = new Set([
      ...snap.net.places.map((p) => p.name),
      ...snap.net.transitions.map((t) => t.name),
    ]);
    for (const name of names) {
      expect(snap.positions[name]).toBeDefined();
    }
  });
});
