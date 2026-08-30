/**
 * Examples + gallery data (design_001 §8; A12, D5).
 *
 * The 3 canonical shared examples, bundled as raw text — these ?raw imports
 * are the ONLY coupling outside tools/petri-net-studio (project D5: the
 * format is the contract). scripts/check-independence.mjs allowlists exactly
 * the `shared/petri-net/examples/` and `shared/petri-net/conformance/`
 * specifier substrings (C7); vite.config.ts `server.fs.allow: ["../.."]` lets
 * the dev server read them.
 *
 * GALLERY_ENTRIES: 8 cards in display order — the 3 canonical examples plus
 * 5 unique fixture nets extracted from the conformance-vector corpus
 * (`JSON.parse(raw).net` re-stringified, preserving canonical member order).
 * `two_way_cycle_truncated` is EXCLUDED (same net as `two_way_cycle`).
 */
import hello from "../../../shared/petri-net/examples/hello.json?raw";
import producerConsumer from "../../../shared/petri-net/examples/producer_consumer.json?raw";
import weightedReaction from "../../../shared/petri-net/examples/weighted_reaction.json?raw";
import twoWayCycleRaw from "../../../shared/petri-net/conformance/analysis-v1/two_way_cycle.json?raw";
import unboundedNetRaw from "../../../shared/petri-net/conformance/analysis-v1/unbounded_net.json?raw";
import deadlockNetRaw from "../../../shared/petri-net/conformance/analysis-v1/deadlock_net.json?raw";
import tokenDrainNetRaw from "../../../shared/petri-net/conformance/analysis-v1/token_drain_net.json?raw";
import twoDeadlocksNetRaw from "../../../shared/petri-net/conformance/analysis-v1/two_deadlocks_net.json?raw";

/** Extract the canonical petri-net-json doc from a conformance vector file. */
function netTextFromVector(raw: string): string {
  return JSON.stringify(JSON.parse(raw).net);
}

const twoWayCycle = netTextFromVector(twoWayCycleRaw);
const unboundedNet = netTextFromVector(unboundedNetRaw);
const deadlockNet = netTextFromVector(deadlockNetRaw);
const tokenDrainNet = netTextFromVector(tokenDrainNetRaw);
const twoDeadlocksNet = netTextFromVector(twoDeadlocksNetRaw);

/** Example name → canonical file bytes (loadExample/importJson source). */
export const EXAMPLE_TEXTS: Record<string, string> = {
  hello,
  producer_consumer: producerConsumer,
  weighted_reaction: weightedReaction,
  two_way_cycle: twoWayCycle,
  unbounded_net: unboundedNet,
  deadlock_net: deadlockNet,
  token_drain_net: tokenDrainNet,
  two_deadlocks_net: twoDeadlocksNet,
};

/** Display/load order for the Examples menu (select path — stays 3). */
export const EXAMPLE_NAMES: string[] = ["hello", "producer_consumer", "weighted_reaction"];

/** Gallery card contract (design_001 §8) — description is studio-local copy. */
export interface GalleryEntry {
  id: string;
  text: string;
  description: string;
}

/** Gallery display order (design_001 §8 — 8 entries; two_way_cycle_truncated excluded). */
export const GALLERY_ENTRIES: GalleryEntry[] = [
  { id: "hello", text: hello, description: "A single enabled step from p1 to p2." },
  {
    id: "producer_consumer",
    text: producerConsumer,
    description: "Producers and consumers sharing a bounded buffer.",
  },
  {
    id: "weighted_reaction",
    text: weightedReaction,
    description: "A weighted reaction: 2H2 + O2 -> 2H2O.",
  },
  {
    id: "two_way_cycle",
    text: twoWayCycle,
    description: "A token cycles forever through two transitions.",
  },
  {
    id: "unbounded_net",
    text: unboundedNet,
    description: "One transition doubles a token — an unbounded net.",
  },
  {
    id: "deadlock_net",
    text: deadlockNet,
    description: "A transition that can never fire — dead at M0.",
  },
  {
    id: "token_drain_net",
    text: tokenDrainNet,
    description: "A token drains to a final deadlock state.",
  },
  {
    id: "two_deadlocks_net",
    text: twoDeadlocksNet,
    description: "Two branches from M0 each end in a distinct deadlock.",
  },
];