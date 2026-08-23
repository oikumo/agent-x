/**
 * Weighted Place/Transition Petri-net model layer — TS port of
 * `src/agentx/model/petri_net/model.py` (executable spec; 60-test matrix in
 * `tests/engine/model.test.ts`). Semantics pinned by design_001 §5:
 *
 * - M'(p) = M(p) − W(p,t) + W(t,p) for a fired transition t.
 * - Enabledness is an AND over all input arcs (vacuously true for no-input
 *   transitions); firing is atomic; disabled firing raises TransitionNotEnabledError.
 * - fireMarking is pure (net and input marking untouched); fire is the mutable
 *   convenience applying the same check against the live marking.
 * - Canonical ordering: placeOrder/transitionOrder are code-point-sorted (A3);
 *   markings are immutable arrays over placeOrder.
 *
 * Edge-case policy (parity): self-loops legal; no-input transitions always
 * enabled; no-output transitions legal; parallel transitions distinct by name;
 * zero-token places meaningful; the empty net is allowed; duplicate arcs rejected.
 */

import {
  DuplicateArcError,
  DuplicatePlaceError,
  InvalidModelError,
  PetriNetError,
  TransitionNotEnabledError,
  UnknownPlaceError,
  UnknownTransitionError,
  ValueError,
} from "./errors.js";

/** Marking = tuple[int, ...] equivalent — immutable by convention. */
export type Marking = readonly number[];

/** Lexicographic by Unicode code point (A3 — NOT JS default UTF-16 sort). */
export function compareCodePoints(a: string, b: string): number {
// TA: why: Code-point comparator, NOT JS default sort: UTF-16 code-unit order diverges from code-point order for astral-plane chars (U+10000+ start with high surrogate < U+FFFF). FORMAT.md §8.5's equivalence claim is an erratum candidate (spec LOCKED — primary rule = code point; surfaced to user, no edit without re-lock). Python sorted() = code points = the semantic reference.
  const ca = [...a];
  const cb = [...b];
  const n = Math.min(ca.length, cb.length);
  for (let i = 0; i < n; i++) {
    const d = ca[i].codePointAt(0)! - cb[i].codePointAt(0)!;
    if (d !== 0) return d;
  }
  return ca.length - cb.length;
}

function isInt(x: unknown): x is number {
  return typeof x === "number" && Number.isInteger(x);
}

export class PetriNet {
  readonly places: Set<string> = new Set();
  readonly transitions: Set<string> = new Set();
  /** transition -> {place: weight} (pre-set •t). */
  readonly inputs: Map<string, Map<string, number>> = new Map();
  /** transition -> {place: weight} (post-set t•). */
  readonly outputs: Map<string, Map<string, number>> = new Map();
  /** Live marking. */
  marking: Map<string, number> = new Map();
  /** M0 — what reset() restores. */
  readonly initialMarking: Map<string, number> = new Map();

  // ------------------------------------------------------------------
  // Mutation API (add-only, build-once)
  // ------------------------------------------------------------------

  addPlace(name: string, tokens: number = 0): void {
    if (!name) throw new ValueError("Place name cannot be empty");
    if (typeof tokens === "boolean" || !isInt(tokens) || tokens < 0) {
      throw new ValueError("Token count must be a non-negative integer");
    }
    if (this.places.has(name)) {
      throw new DuplicatePlaceError(`Place already exists: ${name}`);
    }
    this.places.add(name);
    this.marking.set(name, tokens);
    this.initialMarking.set(name, tokens);
  }

  addTransition(name: string): void {
    if (!name) throw new ValueError("Transition name cannot be empty");
    if (this.transitions.has(name)) {
      // F4 asymmetry: duplicate transition is a plain ValueError.
      throw new ValueError(`Transition already exists: ${name}`);
    }
    this.transitions.add(name);
    this.inputs.set(name, new Map());
    this.outputs.set(name, new Map());
  }

  addInput({ place, transition, weight = 1 }: { place: string; transition: string; weight?: number }): void {
    this.validateArc(place, transition, weight);
    const ins = this.inputs.get(transition)!;
    if (ins.has(place)) {
      throw new DuplicateArcError(`Input arc already exists: ${place} -> ${transition}`);
    }
    ins.set(place, weight);
  }

  addOutput({ transition, place, weight = 1 }: { transition: string; place: string; weight?: number }): void {
    // Object args pin the §9 argument-order gotcha structurally (A5).
    this.validateArc(place, transition, weight);
    const outs = this.outputs.get(transition)!;
    if (outs.has(place)) {
      throw new DuplicateArcError(`Output arc already exists: ${transition} -> ${place}`);
    }
    outs.set(place, weight);
  }

  private validateArc(place: string, transition: string, weight: number): void {
    if (!this.places.has(place)) throw new UnknownPlaceError(place);
    if (!this.transitions.has(transition)) throw new UnknownTransitionError(transition);
    if (typeof weight === "boolean" || !isInt(weight) || weight <= 0) {
      throw new ValueError("Arc weight must be a positive integer");
    }
  }

  private requireTransition(transition: string): void {
    if (!this.transitions.has(transition)) throw new UnknownTransitionError(transition);
  }

  // ------------------------------------------------------------------
  // Order / marking API
  // ------------------------------------------------------------------

  get placeOrder(): string[] {
    return [...this.places].sort(compareCodePoints);
  }

  get transitionOrder(): string[] {
    return [...this.transitions].sort(compareCodePoints);
  }

  get placeIndex(): Map<string, number> {
    return new Map(this.placeOrder.map((p, i) => [p, i]));
  }

  currentMarking(): number[] {
    return this.placeOrder.map((p) => this.marking.get(p)!);
  }

  initialMarkingTuple(): number[] {
    return this.placeOrder.map((p) => this.initialMarking.get(p)!);
  }

  markingToDict(marking: Marking): Map<string, number> {
    if (marking.length !== this.places.size) {
      throw new ValueError("Marking length does not match place count");
    }
    if (marking.some((tokens) => tokens < 0)) {
      throw new ValueError("Marking contains a negative token count");
    }
    return new Map(this.placeOrder.map((p, i) => [p, marking[i]]));
  }

  // ------------------------------------------------------------------
  // Execution API
  // ------------------------------------------------------------------

  isEnabledAt(marking: Marking, transition: string): boolean {
    this.requireTransition(transition);
    const m = this.markingToDict(marking); // validation propagates (ValueError)
    for (const [p, w] of this.inputs.get(transition)!) {
      if (m.get(p)! < w) return false;
    }
    return true;
  }

  enabledTransitionsAt(marking: Marking): string[] {
    return this.transitionOrder.filter((t) => this.isEnabledAt(marking, t));
  }

  /**
   * Pure firing: return the successor marking; raise when disabled.
   * Error precedence (must-pin): UnknownTransitionError, then marking
   * ValueError, then TransitionNotEnabledError. Never mutates.
   */
  fireMarking(marking: Marking, transition: string): number[] {
    this.requireTransition(transition);
    if (!this.isEnabledAt(marking, transition)) {
      throw new TransitionNotEnabledError(transition);
    }
    const index = this.placeIndex;
    const result = [...marking];
    for (const [place, weight] of this.inputs.get(transition)!) {
      result[index.get(place)!] -= weight;
    }
    for (const [place, weight] of this.outputs.get(transition)!) {
      result[index.get(place)!] += weight;
    }
    return result;
  }

  /** Mutable convenience: apply fireMarking to the live marking. */
  fire(transition: string): void {
    this.marking = this.markingToDict(this.fireMarking(this.currentMarking(), transition));
  }

  /** Restore the initial marking M0 (structure untouched). */
  reset(): void {
    this.marking = new Map(this.initialMarking);
  }

  // ------------------------------------------------------------------
  // Structural queries
  // ------------------------------------------------------------------

  /** Transition -> input places; place -> producer transitions. */
  preSet(node: string): Set<string> {
    const [inPlaces, inTransitions] = this.dispatch(node);
    if (inTransitions) return new Set(this.inputs.get(node)!.keys());
    void inPlaces;
    return new Set(this.transitionOrder.filter((t) => this.outputs.get(t)!.has(node)));
  }

  /** Transition -> output places; place -> consumer transitions. */
  postSet(node: string): Set<string> {
    const [, inTransitions] = this.dispatch(node);
    if (inTransitions) return new Set(this.outputs.get(node)!.keys());
    return new Set(this.transitionOrder.filter((t) => this.inputs.get(t)!.has(node)));
  }

  private dispatch(node: string): [boolean, boolean] {
    const inPlaces = this.places.has(node);
    const inTransitions = this.transitions.has(node);
    if (inPlaces && inTransitions) {
      throw new InvalidModelError(`Ambiguous node name: ${node}`);
    }
    if (!inPlaces && !inTransitions) {
      throw new PetriNetError(`Unknown node: ${node}`);
    }
    return [inPlaces, inTransitions];
  }
}
