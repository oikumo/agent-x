/**
 * The 3 canonical shared examples, bundled as raw text (design A12).
 *
 * These ?raw imports are the ONLY coupling outside tools/petri-net-studio
 * (project D5: the format is the contract). scripts/check-independence.mjs
 * allowlists exactly the `shared/petri-net/examples/` specifier substring;
 * vite.config.ts `server.fs.allow: ["../.."]` lets the dev server read them.
 */
import hello from "../../../shared/petri-net/examples/hello.json?raw";
import producerConsumer from "../../../shared/petri-net/examples/producer_consumer.json?raw";
import weightedReaction from "../../../shared/petri-net/examples/weighted_reaction.json?raw";

/** Example name → canonical file bytes. */
export const EXAMPLE_TEXTS: Record<string, string> = {
  hello,
  producer_consumer: producerConsumer,
  weighted_reaction: weightedReaction,
};

/** Display/load order for the Examples menu. */
export const EXAMPLE_NAMES: string[] = ["hello", "producer_consumer", "weighted_reaction"];
