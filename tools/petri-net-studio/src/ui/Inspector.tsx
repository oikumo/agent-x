/**
 * Inspector — selection panel (design §7), rendered in edit mode only.
 *
 * Place: rename (V1 collision-checked by the store), M0 tokens, delete.
 * Transition: rename, delete. Arc: weight (≥ 1), delete. Fields commit on
 * Enter/blur; a rejected commit reverts the field and shows a transient hint.
 * The panel remounts per selection (key on selection id) so local field
 * state always initializes from the committed model.
 */

import { useState } from "react";
import { useStudioStore } from "../state/store.js";

function TextField(props: { label: string; value: string; onCommit: (v: string) => boolean }) {
  const [text, setText] = useState(props.value);
  const [rejected, setRejected] = useState(false);
  const commit = () => {
    if (text === props.value) return;
    const ok = props.onCommit(text);
    setRejected(!ok);
    if (!ok) setText(props.value);
  };
  return (
    <label className="field">
      <span>{props.label}</span>
      <input
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setRejected(false);
        }}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") (e.target as HTMLInputElement).blur();
        }}
      />
      {rejected && <span className="field-error">rejected (empty or duplicate)</span>}
    </label>
  );
}

function NumberField(props: { label: string; value: number; min: number; onCommit: (n: number) => boolean }) {
  const [text, setText] = useState(String(props.value));
  const [rejected, setRejected] = useState(false);
  const commit = () => {
    const n = Number(text);
    if (String(n) === text && Number.isInteger(n) && n >= props.min && props.onCommit(n)) {
      setRejected(false);
      return;
    }
    setRejected(true);
    setText(String(props.value));
  };
  return (
    <label className="field">
      <span>{props.label}</span>
      <input
        type="number"
        min={props.min}
        step={1}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setRejected(false);
        }}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") (e.target as HTMLInputElement).blur();
        }}
      />
      {rejected && <span className="field-error">must be an integer ≥ {props.min}</span>}
    </label>
  );
}

export function Inspector() {
  const mode = useStudioStore((s) => s.mode);
  const selection = useStudioStore((s) => s.selection);
  const doc = useStudioStore((s) => s.doc);
  const renameNode = useStudioStore((s) => s.renameNode);
  const setTokens = useStudioStore((s) => s.setTokens);
  const setWeight = useStudioStore((s) => s.setWeight);
  const removeNode = useStudioStore((s) => s.removeNode);
  const removeArc = useStudioStore((s) => s.removeArc);

  if (mode !== "edit" || selection === null) return null;

  if (selection.kind === "arc") {
    const [source, target] = JSON.parse(selection.id) as [string, string];
    const arc = doc.arcs.find((a) => a.source === source && a.target === target);
    if (!arc) return null;
    return (
      <aside className="inspector" key={selection.id}>
        <h2>Arc</h2>
        <p className="inspector-sub">
          {source} → {target}
        </p>
        <NumberField
          label="weight"
          value={arc.weight}
          min={1}
          onCommit={(n) => setWeight(source, target, n)}
        />
        <button className="danger" onClick={() => removeArc(source, target)}>
          Delete arc
        </button>
      </aside>
    );
  }

  const name = selection.id;
  const isPlace = selection.kind === "place";
  const nodeExists = isPlace
    ? doc.places.some((p) => p.name === name)
    : doc.transitions.some((t) => t.name === name);
  if (!nodeExists) return null;
  const tokens = isPlace ? doc.places.find((p) => p.name === name)!.tokens : 0;

  return (
    <aside className="inspector" key={`${selection.kind}:${name}`}>
      <h2>{isPlace ? "Place" : "Transition"}</h2>
      <TextField label="name" value={name} onCommit={(v) => renameNode(name, v)} />
      {isPlace && (
        <NumberField label="tokens (M0)" value={tokens} min={0} onCommit={(n) => setTokens(name, n)} />
      )}
      <button className="danger" onClick={() => removeNode(name)}>
        Delete {isPlace ? "place" : "transition"}
      </button>
    </aside>
  );
}
