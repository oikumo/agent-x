// @vitest-environment node
/**
 * Gallery metadata tests — design_001 §10.3.
 *
 * GALLERY_ENTRIES: 8 entries (3 canonical shared examples + 5 fixture nets
 * from the conformance vector corpus); ids unique; every entry's `text`
 * parses via `documentFromJson` (schema-valid canonical petri-net-json);
 * `loadExample(id)` succeeds for EVERY gallery id (EXAMPLE_TEXTS extension);
 * descriptions non-empty; `two_way_cycle_truncated` excluded.
 */

import { beforeEach, describe, expect, it } from "vitest";

import { documentFromJson } from "../../src/engine/io.js";
import { GALLERY_ENTRIES, EXAMPLE_NAMES, EXAMPLE_TEXTS } from "../../src/examples.js";
import { initialDataState, useStudioStore } from "../../src/state/store.js";

beforeEach(() => {
  useStudioStore.setState(initialDataState());
});

const GALLERY_IDS = GALLERY_ENTRIES.map((e) => e.id);

describe("Gallery metadata", () => {
  it("has exactly 8 entries in the pinned display order", () => {
    expect(GALLERY_IDS).toEqual([
      "hello",
      "producer_consumer",
      "weighted_reaction",
      "two_way_cycle",
      "unbounded_net",
      "deadlock_net",
      "token_drain_net",
      "two_deadlocks_net",
    ]);
  });

  it("ids are unique", () => {
    expect(new Set(GALLERY_IDS).size).toBe(GALLERY_IDS.length);
  });

  it("every entry text parses via documentFromJson (schema-valid canonical)", () => {
    for (const entry of GALLERY_ENTRIES) {
      expect(() => documentFromJson(entry.text)).not.toThrow();
    }
  });

  it("every description is non-empty", () => {
    for (const entry of GALLERY_ENTRIES) {
      expect(entry.description.length).toBeGreaterThan(0);
    }
  });

  it("two_way_cycle_truncated is excluded", () => {
    expect(GALLERY_IDS).not.toContain("two_way_cycle_truncated");
  });
});

describe("Gallery load path", () => {
  it("loadExample succeeds for every gallery id", () => {
    const store = useStudioStore.getState();
    for (const id of GALLERY_IDS) {
      expect(store.loadExample(id)).toBe(true);
      expect(useStudioStore.getState().importError).toBeNull();
    }
  });

  it("EXAMPLE_NAMES stays the 3 canonical examples (select path unchanged)", () => {
    expect(EXAMPLE_NAMES).toEqual(["hello", "producer_consumer", "weighted_reaction"]);
  });

  it("EXAMPLE_TEXTS covers all gallery ids", () => {
    for (const id of GALLERY_IDS) {
      expect(EXAMPLE_TEXTS[id]).toBeDefined();
    }
  });
});