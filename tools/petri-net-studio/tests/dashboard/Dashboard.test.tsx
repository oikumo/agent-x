/**
 * Dashboard render — feature_043 (operation_spec_001 Dashboard contract).
 *
 * Read-only view over a fixture snapshot: header pool counts, revision
 * slider bounded by the snapshot list, slider steps change place token text,
 * blocked places carry the `blocked` class. Default env is jsdom.
 */

import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { ReactFlowProvider } from "@xyflow/react";
import { afterEach, beforeAll, describe, expect, it } from "vitest";

import { Dashboard } from "../../src/dashboard/Dashboard.js";

afterEach(() => cleanup());

beforeAll(() => {
  // jsdom lacks ResizeObserver (ReactFlow needs it at render).
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
});

const FIXTURE = {
  format: "meta-net-dashboard-snapshot",
  version: 1,
  net_revision: 2,
  built_at: "2026-09-05T00:00:00+00:00",
  place_order: ["agent_attention", "feature_ready", "work_active", "work_pending"],
  net: {
    places: [
      { name: "agent_attention", tokens: 1 },
      { name: "feature_ready", tokens: 1 },
      { name: "work_active", tokens: 0 },
      { name: "work_pending", tokens: 1 },
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
  },
  positions: {
    agent_attention: { x: 0, y: 0 },
    feature_ready: { x: 180, y: 0 },
    work_active: { x: 360, y: 0 },
    work_pending: { x: 540, y: 0 },
    work_start: { x: 90, y: 140 },
    work_complete: { x: 270, y: 140 },
  },
  pool: { pending: 1, active: 0, done: 0 },
  skipped: [],
  snapshots: [
    {
      revision: 1,
      kind: "net_fire",
      label: "boot",
      marking: { agent_attention: 1, feature_ready: 1, work_active: 0, work_pending: 0 },
    },
    {
      revision: 2,
      kind: "net_fire",
      label: "work_start",
      marking: { agent_attention: 0, feature_ready: 1, work_active: 1, work_pending: 0 },
    },
  ],
};

function renderDashboard() {
  return render(
    <ReactFlowProvider>
      <Dashboard snapshot={FIXTURE} />
    </ReactFlowProvider>,
  );
}

describe("Dashboard", () => {
  it("shows pool counts and a slider bounded by the snapshot list", () => {
    renderDashboard();
    expect(screen.getByTestId("pool-line")).toHaveTextContent("pending=1");
    const slider = screen.getByTestId("revision-slider") as HTMLInputElement;
    expect(slider.max).toBe("1");
    expect(screen.getByTestId("revision-label")).toHaveTextContent("rev 2");
  });

  it("slider steps change place token text; blocked class marks empty inputs", () => {
    renderDashboard();
    expect(screen.getByTestId("place-work_active")).toHaveTextContent("1");
    const slider = screen.getByTestId("revision-slider");
    fireEvent.change(slider, { target: { value: "0" } });
    expect(screen.getByTestId("place-work_active")).toHaveTextContent("0");
    expect(screen.getByTestId("revision-label")).toHaveTextContent("rev 1");
    fireEvent.change(slider, { target: { value: "1" } });
    expect(screen.getByTestId("place-work_active")).toHaveTextContent("1");
    // attention held at rev 2 → work_start blocked by agent_attention
    expect(document.querySelector(".blocked")).not.toBeNull();
  });
});
