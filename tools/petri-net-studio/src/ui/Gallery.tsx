/**
 * Gallery — example-card grid (design_001 §8; feature_036).
 *
 * Toggle panel (`galleryOpen` is App-local — pure UI chrome, C6): a grid of
 * cards over GALLERY_ENTRIES (3 canonical examples + 5 conformance fixture
 * nets). Load reuses the existing `store.loadExample(id)` path (→ edit mode);
 * import failures surface via the existing `importError` banner.
 */

import { GALLERY_ENTRIES } from "../examples.js";
import { useStudioStore } from "../state/store.js";

export function Gallery(props: { onClose: () => void }) {
  const loadExample = useStudioStore((s) => s.loadExample);
  return (
    <div className="dialog-backdrop" onClick={props.onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>Example gallery</h2>
        <div className="gallery-grid">
          {GALLERY_ENTRIES.map((entry) => (
            <div key={entry.id} className="gallery-card">
              <h3>{entry.id}</h3>
              <p>{entry.description}</p>
              <button
                className="primary"
                onClick={() => {
                  loadExample(entry.id);
                  props.onClose();
                }}
              >
                Load
              </button>
            </div>
          ))}
        </div>
        <div className="dialog-row">
          <button onClick={props.onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}