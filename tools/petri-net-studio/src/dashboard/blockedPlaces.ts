/**
 * Blocked-place computation — feature_043 (operation_spec_001, pure DOM-free).
 *
 * For each disabled transition, report its empty input places (sorted,
 * deduped); `deadlocked` iff no transition is enabled. Engine semantics come
 * from `toNet(doc)` — no new net logic (operation_spec global invariant).
 */

import { toNet } from "../state/document.js";
import type { NetDocument } from "../state/document.js";

export interface Blockage {
  blocked: string[];
  deadlocked: boolean;
}

export function blockedPlaces(doc: NetDocument, marking: number[]): Blockage {
  const net = toNet(doc);
  const index = net.placeIndex;
  const blocked = new Set<string>();
  let anyEnabled = false;
  for (const t of net.transitionOrder) {
    if (net.isEnabledAt(marking, t)) {
      anyEnabled = true;
      continue;
    }
    for (const [p, w] of net.inputs.get(t)!) {
      if ((marking[index.get(p)!] ?? 0) < w) blocked.add(p);
    }
  }
  return {
    blocked: [...blocked].sort(),
    deadlocked: !anyEnabled,
  };
}
