/**
 * Analysis layer — TS port of `src/agentx/model/petri_net/analysis.py`
 * (executable spec; 38 behaviors in `tests/engine/analysis.test.ts`).
 * Semantics pinned by design_001 §5: exact parity B2/B3, deterministic
 * ordering B6, no overclaiming (truncation → value null/complete false).
 *
 * Port notes:
 * - B1: markings keyed by `markingKey(m) = m.join(",")` (non-negative ints
 *   ⇒ unambiguous). Results re-materialize arrays from keys in deterministic
 *   (compareMarkings-sorted) order.
 * - B2: `nullspace` copies analysis.py line-for-line (Fraction Gauss–Jordan
 *   to FULL RREF); `_coprimeIntVector` mirrors `_coprime_int_vector`
 *   (LCM-scale → gcd-content divide → negate if first nonzero negative).
 *   No floats in the algebra path (fraction.ts).
 * - B3: `explore` copies the Python `_explore` loop 1:1 — edge-recording +
 *   no-enqueue + `complete=false` + finish-current-state-edges + break.
 * - B7: Tarjan skips edge targets outside `graph.states` (truncation-only
 *   dangling references — no phantom single-state components).
 */

import { PetriNet, Marking } from "./model.js";
import { Fraction, gcd, lcm } from "./fraction.js";

/** B1 — markings are non-negative ints ⇒ join(",") is unambiguous. */
export function markingKey(m: Marking): string {
  return m.join(",");
}

/** Key → marking (complement of markingKey; empty marking ⇒ []). */
export function markingFromKey(key: string): number[] {
// TA: gotcha: gotcha: markingFromKey must special-case the empty marking — markingKey([]) = "" and "".split(",") would yield [""] → [0] (wrong). The empty net's single SCC component must be [[]] not [[0]].
  return key === "" ? [] : key.split(",").map(Number);
}

/** Numeric lexicographic — Python tuple ordering (B6). */
export function compareMarkings(a: Marking, b: Marking): number {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return a.length - b.length;
}

export interface AnalysisResult {
  value: boolean | null;
  complete: boolean;
  exploredStates: number;
  reason?: string | null;
}

export interface ReachabilityResult {
  markings: number[][];
  predecessors: Map<string, { prev: number[] | null; transition: string | null }>;
  complete: boolean;
  exploredStates: number;
}

export interface ReachabilityGraph {
  states: number[][];
  edges: Map<string, Array<[string, number[]]>>;
  complete: boolean;
}

export interface DeadlockResult {
  deadlocks: number[][];
  complete: boolean;
  exploredStates: number;
  reason?: string | null;
}

export interface BoundResult {
  bounded: boolean | null;
  bounds: Array<[string, number]>;
  complete: boolean;
  reason?: string | null;
}

interface ExploreOut {
  visitedMarkings: number[][];
  predecessors: Map<string, { prev: number[] | null; transition: string | null }>;
  edges: Map<string, Array<[string, number[]]>>;
  complete: boolean;
  exploredStates: number;
}

const TRUNCATED_DEADLOCK_REASON =
  "State-space exploration was truncated; " +
  "listed deadlocks are only those among explored states.";
const TRUNCATED_BOUNDS_REASON =
  "State-space exploration was truncated; boundedness is unknown.";
const INCOMPLETE_LIVENESS_REASON =
  "Reachability graph is incomplete; liveness is unknown.";
const INCOMPLETE_GLOBAL_LIVENESS_REASON =
  "Reachability graph is incomplete; global liveness is unknown.";

export class PetriNetAnalyzer {
  constructor(readonly net: PetriNet) {}

  // ------------------------------------------------------------------
  // Shared BFS exploration core (§31 — B3: 1:1 port of Python _explore)
  // ------------------------------------------------------------------

  private explore(maxStates: number | null): ExploreOut {
    const net = this.net;
    const initial = net.initialMarkingTuple();
    const queue: number[][] = [initial];
    const visited = new Map<string, number[]>();
    const initialKey = markingKey(initial);
    visited.set(initialKey, initial);
    const predecessors = new Map<
      string,
      { prev: number[] | null; transition: string | null }
    >();
    predecessors.set(initialKey, { prev: null, transition: null });
    const edges = new Map<string, Array<[string, number[]]>>();
    let complete = true;
    let qi = 0;
    while (qi < queue.length) {
      const marking = queue[qi++];
      const outgoing: Array<[string, number[]]> = [];
      for (const transition of net.enabledTransitionsAt(marking)) {
        const successor = net.fireMarking(marking, transition);
        outgoing.push([transition, successor]);
        const skey = markingKey(successor);
        if (visited.has(skey)) {
          continue;
        }
        if (maxStates !== null && visited.size >= maxStates) {
          complete = false;
          continue;
        }
        visited.set(skey, successor);
        predecessors.set(skey, { prev: marking, transition });
        queue.push(successor);
      }
      edges.set(markingKey(marking), outgoing);
      if (!complete) {
        break;
      }
    }
    return {
      visitedMarkings: [...visited.values()],
      predecessors,
      edges,
      complete,
      exploredStates: visited.size,
    };
  }

  // ------------------------------------------------------------------
  // Exploration APIs (B6: markings/states sorted by compareMarkings)
  // ------------------------------------------------------------------

  reachableMarkings(maxStates: number | null): ReachabilityResult {
    const { visitedMarkings, predecessors, complete, exploredStates } =
      this.explore(maxStates);
    return {
      markings: [...visitedMarkings].sort(compareMarkings),
      predecessors,
      complete,
      exploredStates,
    };
  }

  reachabilityGraph(maxStates: number | null): ReachabilityGraph {
    const { visitedMarkings, edges, complete } = this.explore(maxStates);
    return {
      states: [...visitedMarkings].sort(compareMarkings),
      edges,
      complete,
    };
  }

  deadlocks(maxStates: number | null): DeadlockResult {
    const { visitedMarkings, complete, exploredStates } = this.explore(maxStates);
    const deadlocks = visitedMarkings
      .filter((m) => this.net.enabledTransitionsAt(m).length === 0)
      .sort(compareMarkings);
    return {
      deadlocks,
      complete,
      exploredStates,
      reason: complete ? null : TRUNCATED_DEADLOCK_REASON,
    };
  }

  bounds(maxStates: number | null): BoundResult {
    const { visitedMarkings, complete } = this.explore(maxStates);
    const placeOrder = this.net.placeOrder;
    const maxima = new Map<string, number>(placeOrder.map((p) => [p, 0]));
    for (const marking of visitedMarkings) {
      for (let i = 0; i < marking.length; i++) {
        const place = placeOrder[i];
        if (marking[i] > (maxima.get(place) ?? 0)) {
          maxima.set(place, marking[i]);
        }
      }
    }
    const bounds = placeOrder.map((p) => [p, maxima.get(p)!] as [string, number]);
    if (complete) {
      return { bounded: true, bounds, complete: true, reason: null };
    }
    return {
      bounded: null,
      bounds,
      complete: false,
      reason: TRUNCATED_BOUNDS_REASON,
    };
  }

  // ------------------------------------------------------------------
  // Graph-driven APIs (no exploration; §32)
  // ------------------------------------------------------------------

  firingSequenceTo(result: ReachabilityResult, target: number[]): string[] | null {
    const tkey = markingKey(target);
    // null is a PROOF of unreachability only when result.complete is true.
    if (!result.markings.some((m) => markingKey(m) === tkey)) {
      return null;
    }
    const sequence: string[] = [];
    let current = target;
    while (true) {
      const entry = result.predecessors.get(markingKey(current))!;
      const { prev, transition } = entry;
      if (prev === null) {
        break;
      }
      sequence.push(transition!);
      current = prev;
    }
    sequence.reverse();
    return sequence;
  }

  transitionLiveness(transition: string, graph: ReachabilityGraph): AnalysisResult {
    // Incomplete graph -> value null (unknown), never a bare bool.
    if (!graph.complete) {
      return {
        value: null,
        complete: false,
        exploredStates: graph.states.length,
        reason: INCOMPLETE_LIVENESS_REASON,
      };
    }
    const enabling = graph.states.filter((s) => this.net.isEnabledAt(s, transition));
    if (enabling.length === 0) {
      return {
        value: false,
        complete: true,
        exploredStates: graph.states.length,
        reason: null,
      };
    }
    const reverse = new Map<string, number[][]>(
      graph.states.map((s) => [markingKey(s), []]),
    );
    for (const state of [...graph.states].sort(compareMarkings)) {
      for (const [, successor] of graph.edges.get(markingKey(state)) ?? []) {
        const skey = markingKey(successor);
        if (reverse.has(skey)) {
          reverse.get(skey)!.push(state);
        }
      }
    }
    const canReach = new Set<string>(enabling.map(markingKey));
    const stack = [...enabling].sort(compareMarkings).map(markingKey);
    while (stack.length > 0) {
      const state = stack.pop()!;
      for (const predecessor of reverse.get(state) ?? []) {
        const pkey = markingKey(predecessor);
        if (!canReach.has(pkey)) {
          canReach.add(pkey);
          stack.push(pkey);
        }
      }
    }
    return {
      value: canReach.size === graph.states.length,
      complete: true,
      exploredStates: graph.states.length,
      reason: null,
    };
  }

  isLive(graph: ReachabilityGraph): AnalysisResult {
    if (!graph.complete) {
      return {
        value: null,
        complete: false,
        exploredStates: graph.states.length,
        reason: INCOMPLETE_GLOBAL_LIVENESS_REASON,
      };
    }
    for (const transition of this.net.transitionOrder) {
      const result = this.transitionLiveness(transition, graph);
      if (result.value !== true) {
        return result;
      }
    }
    // Empty net: no transitions ⇒ AnalysisResult(True, True, 1) (F1).
    return {
      value: true,
      complete: true,
      exploredStates: graph.states.length,
      reason: null,
    };
  }

  stronglyConnectedComponents(graph: ReachabilityGraph): number[][][] {
    // Tarjan SCCs over the graph's vertex set (§23, B7). Recursive (depth
    // fine for v1 nets). Neighbors followed in edge-tuple order, start nodes
    // in sorted-state order; edge targets outside graph.states are skipped.
    const indices = new Map<string, number>();
    const lowlinks = new Map<string, number>();
    const onStack = new Set<string>();
    const stack: string[] = [];
    const components: number[][][] = [];
    let counter = 0;
    const states = new Set<string>(graph.states.map(markingKey));

    const strongconnect = (v: number[]): void => {
      const vkey = markingKey(v);
      indices.set(vkey, counter);
      lowlinks.set(vkey, counter);
      counter += 1;
      stack.push(vkey);
      onStack.add(vkey);
      for (const [, w] of graph.edges.get(vkey) ?? []) {
        const wkey = markingKey(w);
        if (!states.has(wkey)) {
          continue;
        }
        if (!indices.has(wkey)) {
          strongconnect(w);
          lowlinks.set(vkey, Math.min(lowlinks.get(vkey)!, lowlinks.get(wkey)!));
        } else if (onStack.has(wkey)) {
          lowlinks.set(vkey, Math.min(lowlinks.get(vkey)!, indices.get(wkey)!));
        }
      }
      if (lowlinks.get(vkey) === indices.get(vkey)) {
        const component: number[][] = [];
        while (true) {
          const wkey = stack.pop()!;
          onStack.delete(wkey);
          component.push(markingFromKey(wkey));
          if (wkey === vkey) {
            break;
          }
        }
        component.sort(compareMarkings);
        components.push(component);
      }
    };

    for (const v of [...graph.states].sort(compareMarkings)) {
      if (!indices.has(markingKey(v))) {
        strongconnect(v);
      }
    }
    return components;
  }

  // ------------------------------------------------------------------
  // Exact algebra (§7/§18/§19; D4 zero-dependency; F6/F7)
  // ------------------------------------------------------------------

  incidenceMatrix(): number[][] {
    // C[p][t] = W(t,p) - W(p,t); rows=placeOrder, cols=transitionOrder.
    const rows: number[][] = [];
    for (const p of this.net.placeOrder) {
      const row: number[] = [];
      for (const t of this.net.transitionOrder) {
        row.push(
          (this.net.outputs.get(t)?.get(p) ?? 0) -
            (this.net.inputs.get(t)?.get(p) ?? 0),
        );
      }
      rows.push(row);
    }
    return rows;
  }

  placeInvariants(): number[][] {
    // Basis of Cᵀ x = 0 (token-conservation laws), coprime int tuples.
    // Degenerate nets (F7): places-but-no-transitions -> identity basis;
    // empty net -> [].
    const matrix = this.incidenceMatrix();
    const nPlaces = this.net.placeOrder.length;
    if (nPlaces === 0) {
      return [];
    }
    const transposed = matrix.length > 0 ? transpose(matrix) : [];
    return nullspace(transposed, nPlaces).map(_coprimeIntVector);
  }

  transitionInvariants(): number[][] {
    // Basis of C y = 0 (cyclic firing multisets), coprime int tuples.
    // Degenerate nets (F7): transitions-but-no-places -> identity basis;
    // empty net -> [].
    const matrix = this.incidenceMatrix();
    const nTrans = this.net.transitionOrder.length;
    if (nTrans === 0) {
      return [];
    }
    return nullspace(matrix, nTrans).map(_coprimeIntVector);
  }
}

// ---------------------------------------------------------------------------
// Exact rational nullspace (§18 — D4: pure-TS, zero dependencies; B2)
// ---------------------------------------------------------------------------

function transpose(matrix: number[][]): number[][] {
  const cols = matrix.length > 0 ? matrix[0].length : 0;
  const result: number[][] = [];
  for (let c = 0; c < cols; c++) {
    const row: number[] = [];
    for (const r of matrix) {
      row.push(r[c]);
    }
    result.push(row);
  }
  return result;
}

function nullspace(matrix: number[][], nCols?: number): Fraction[][] {
  // Exact nullspace basis via Fraction Gauss–Jordan to FULL RREF (1:1 port
  // of analysis.py). Free columns each emit one basis vector: 1 at the free
  // column, -rows[pivot_row[c]][f] at each pivot column c, 0 elsewhere.
  const rows = matrix.map((row) => row.map((x) => new Fraction(x)));
  const nRows = rows.length;
  let nc = nCols;
  if (nc === undefined) {
    nc = rows.length > 0 ? rows[0].length : 0;
  }
  const pivotRowOfCol = new Map<number, number>();
  let r = 0;
  for (let c = 0; c < nc; c++) {
    let pivot: number | null = null;
    for (let i = r; i < nRows; i++) {
      if (!rows[i][c].isZero()) {
        pivot = i;
        break;
      }
    }
    if (pivot === null) {
      continue;
    }
    [rows[r], rows[pivot]] = [rows[pivot], rows[r]];
    const factor = rows[r][c];
    rows[r] = rows[r].map((x) => x.div(factor));
    for (let i = 0; i < nRows; i++) {
      if (i !== r && !rows[i][c].isZero()) {
        const f = rows[i][c];
        rows[i] = rows[i].map((x, j) => x.sub(f.mul(rows[r][j])));
      }
    }
    pivotRowOfCol.set(c, r);
    r += 1;
    if (r === nRows) {
      break;
    }
  }
  const basis: Fraction[][] = [];
  for (let f = 0; f < nc; f++) {
    if (pivotRowOfCol.has(f)) {
      continue;
    }
    const vec: Fraction[] = new Array(nc).fill(Fraction.zero());
    vec[f] = new Fraction(1);
    for (const [c, pivotRow] of pivotRowOfCol) {
      vec[c] = rows[pivotRow][f].neg();
    }
    basis.push(vec);
  }
  return basis;
}

function _coprimeIntVector(vec: Fraction[]): number[] {
// TA: gotcha: gotcha: JS -x of 0 yields -0, but Python int() canonicalizes -0.0 → 0. Vitest toEqual distinguishes 0/-0 (Object.is). Fixed in Fraction constructor AND _coprimeIntVector final map (v === 0 ? 0 : v). Caught by conformance vector weighted_reaction place_invariants ([1,-0,-2] vs [1,0,-2]).
  // Deterministic integer representative: LCM-scale to ints, divide by the
  // gcd-content, negate when the first nonzero component is negative (§19).
  let l = 1;
  for (const x of vec) {
    l = lcm(l, x.den);
  }
  const ints = vec.map((x) => x.num * (l / x.den));
  let content = 0;
  for (const v of ints) {
    content = gcd(content, Math.abs(v));
  }
  if (content > 1) {
    for (let i = 0; i < ints.length; i++) {
      ints[i] = ints[i] / content;
    }
  }
  for (const v of ints) {
    if (v !== 0) {
      if (v < 0) {
        for (let i = 0; i < ints.length; i++) {
          ints[i] = -ints[i];
        }
      }
      break;
    }
  }
  // Python int canonicalization: -0 normalizes to 0 (JS -x of 0 is -0).
  return ints.map((v) => (v === 0 ? 0 : v));
}