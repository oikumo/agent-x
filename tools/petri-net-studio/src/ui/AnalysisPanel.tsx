/**
 * AnalysisPanel — no-overclaim analysis dashboard (design_001 §9, D10).
 *
 * Derived state only (B12): `useMemo` over `toNet(doc)` + `maxStates` — a
 * structural/M0 edit changes `doc` identity and recomputes; simulate-mode
 * firing does NOT touch `doc`, so the panel always describes the net from
 * its INITIAL marking M0 (labelled below — analysis never depends on the
 * live marking).
 *
 * Every verdict row renders badge (✅ proven / ❌ disproven / ❓ unknown) +
 * `complete` + verbatim `reason`; truncated results are visually distinct
 * and never overclaim. `max_states` dial: number input (min 1) + "unlimited"
 * checkbox, current value always visible (B10).
 */

import { useMemo } from "react";

import { PetriNetAnalyzer, markingKey } from "../engine/analysis.js";
import { toNet } from "../state/document.js";
import { useStudioStore } from "../state/store.js";

function StatusBadge(props: { value: boolean | null; complete: boolean }) {
  const unknown = !props.complete || props.value === null;
  const glyph = unknown ? "❓" : props.value ? "✅" : "❌";
  const cls = unknown ? "status-unknown" : props.value ? "status-ok" : "status-no";
  return <span className={`status-badge ${cls}`} aria-label={glyph}>{glyph}</span>;
}

export function AnalysisPanel() {
  const doc = useStudioStore((s) => s.doc);
  const maxStates = useStudioStore((s) => s.maxStates);
  const setMaxStates = useStudioStore((s) => s.setMaxStates);

  const analysis = useMemo(() => {
    const net = toNet(doc);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(maxStates);
    return {
      net,
      analyzer,
      graph,
      reach: analyzer.reachableMarkings(maxStates),
      deadlocks: analyzer.deadlocks(maxStates),
      bounds: analyzer.bounds(maxStates),
      incidence: analyzer.incidenceMatrix(),
      placeInvariants: analyzer.placeInvariants(),
      transitionInvariants: analyzer.transitionInvariants(),
      isLive: analyzer.isLive(graph),
      sccs: analyzer.stronglyConnectedComponents(graph),
      transitions: net.transitionOrder.map((t) => ({
        name: t,
        result: analyzer.transitionLiveness(t, graph),
      })),
    };
  }, [doc, maxStates]);

  // M0 first, then the remaining reachable markings in sorted order (§9).
  const m0 = analysis.net.initialMarkingTuple();
  const m0Key = markingKey(m0);
  const orderedMarkings = [m0, ...analysis.reach.markings.filter((m) => markingKey(m) !== m0Key)];
  const placeOrder = analysis.net.placeOrder;
  const transitionOrder = analysis.net.transitionOrder;

  return (
    <section className="analysis-panel">
      <h2>
        Analysis <span className="analysis-sub">from initial marking M0</span>
      </h2>

      <div className="analysis-dial">
        <label htmlFor="analysis-max-states">max states</label>
        <input
          id="analysis-max-states"
          type="number"
          min={1}
          step={1}
          value={maxStates === null ? "" : maxStates}
          disabled={maxStates === null}
          onChange={(e) => {
            const n = Number(e.target.value);
            if (Number.isInteger(n) && n >= 1) setMaxStates(n);
          }}
        />
        <label className="analysis-unlimited">
          <input
            type="checkbox"
            checked={maxStates === null}
            onChange={(e) => setMaxStates(e.target.checked ? null : 1000)}
          />
          unlimited
        </label>
        <span className="analysis-dial-text">
          {maxStates === null ? "∞ unlimited exploration" : `cap: ${maxStates} explored state(s)`}
        </span>
      </div>

      <section className="analysis-section">
        <h3>
          Reachability <StatusBadge value={null} complete={analysis.reach.complete} />
        </h3>
        <p className="analysis-count">
          {analysis.reach.exploredStates} state(s) explored ·{" "}
          {analysis.reach.complete ? "complete" : "truncated — results are partial, never a proof"}
        </p>
        <table className="analysis-table">
          <thead>
            <tr>
              <th />
              {placeOrder.map((p) => (
                <th key={p}>{p}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {orderedMarkings.map((m, i) => (
              <tr key={i}>
                <th>{i === 0 ? "M0" : String(i)}</th>
                {m.map((tokens, j) => (
                  <td key={j}>{tokens}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="analysis-section">
        <h3>
          Deadlocks <StatusBadge value={null} complete={analysis.deadlocks.complete} />
        </h3>
        <p className="analysis-count">
          {analysis.deadlocks.deadlocks.length} found among explored states
        </p>
        {analysis.deadlocks.deadlocks.length > 0 && (
          <ul className="analysis-list">
            {analysis.deadlocks.deadlocks.map((m, i) => (
              <li key={i}>({m.join(",")})</li>
            ))}
          </ul>
        )}
        {analysis.deadlocks.reason && (
          <p className="verdict-reason">{analysis.deadlocks.reason}</p>
        )}
      </section>

      <section className="analysis-section">
        <h3>
          Bounds <StatusBadge value={analysis.bounds.bounded} complete={analysis.bounds.complete} />
        </h3>
        <ul className="analysis-list">
          {analysis.bounds.bounds.map(([place, max]) => (
            <li key={place}>
              {place}: {max}
            </li>
          ))}
        </ul>
        {analysis.bounds.reason && <p className="verdict-reason">{analysis.bounds.reason}</p>}
      </section>

      <section className="analysis-section">
        <h3>
          Liveness <StatusBadge value={analysis.isLive.value} complete={analysis.isLive.complete} />
        </h3>
        {analysis.isLive.reason && <p className="verdict-reason">{analysis.isLive.reason}</p>}
        <ul className="analysis-list">
          {analysis.transitions.map(({ name, result }) => (
            <li key={name}>
              <StatusBadge value={result.value} complete={result.complete} /> {name}
            </li>
          ))}
        </ul>
      </section>

      <section className="analysis-section">
        <h3>Strongly connected components</h3>
        <p className="analysis-count">{analysis.sccs.length} component(s)</p>
        {analysis.sccs.map((comp, i) => (
          <div key={i} className="scc-row">
            {comp.map((m) => `(${m.join(",")})`).join(" ")}
          </div>
        ))}
      </section>

      <section className="analysis-section">
        <h3>Place invariants</h3>
        {analysis.placeInvariants.length === 0 ? (
          <p className="analysis-count">none</p>
        ) : (
          <table className="analysis-table">
            <thead>
              <tr>
                <th />
                {placeOrder.map((p) => (
                  <th key={p}>{p}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {analysis.placeInvariants.map((v, i) => (
                <tr key={i}>
                  <th>{i + 1}</th>
                  {v.map((x, j) => (
                    <td key={j}>{x}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="analysis-section">
        <h3>Transition invariants</h3>
        {analysis.transitionInvariants.length === 0 ? (
          <p className="analysis-count">none</p>
        ) : (
          <table className="analysis-table">
            <thead>
              <tr>
                <th />
                {transitionOrder.map((t) => (
                  <th key={t}>{t}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {analysis.transitionInvariants.map((v, i) => (
                <tr key={i}>
                  <th>{i + 1}</th>
                  {v.map((x, j) => (
                    <td key={j}>{x}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="analysis-section">
        <h3>Incidence matrix</h3>
        <table className="analysis-table">
          <thead>
            <tr>
              <th />
              {transitionOrder.map((t) => (
                <th key={t}>{t}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {analysis.incidence.map((row, i) => (
              <tr key={i}>
                <th>{placeOrder[i]}</th>
                {row.map((x, j) => (
                  <td key={j}>{x}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  );
}