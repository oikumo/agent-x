/**
 * Animation sequence helpers (design §5, §11-4; C3, C10) — PURE, DOM-free.
 *
 * `firingSequenceTo` returns M0-rooted transition sequences; these helpers
 * fold `net.fireMarking` (engine-pure semantics — never a UI simulation) to
 * materialize the marking at each step. Animation state (step/playing) lives
 * in the component; this module only derives markings.
 *
 * Null sequences are a CALLER case: the UI renders "unreachable"; these
 * helpers are never called with `null` (operation_spec_001 §animation).
 */

import type { PetriNet } from "../engine/model.js";

/** Marking after firing seq[0..step) from m0; clamped to [0, seq.length]. Returns a NEW array. */
export function markingAt(net: PetriNet, m0: number[], seq: string[], step: number): number[] {
  const k = Math.min(Math.max(step, 0), seq.length);
  let marking = [...m0];
  for (let i = 0; i < k; i++) {
    marking = net.fireMarking(marking, seq[i]);
  }
  return marking;
}

/** [m0, markingAt(1), …, markingAt(seq.length)] — length seq.length + 1. */
export function sequenceSteps(net: PetriNet, m0: number[], seq: string[]): number[][] {
  const steps: number[][] = [];
  for (let i = 0; i <= seq.length; i++) {
    steps.push(markingAt(net, m0, seq, i));
  }
  return steps;
}