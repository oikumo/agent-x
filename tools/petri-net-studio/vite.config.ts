/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    // Allow Vite to serve the repo-level shared/ data files (?raw imports of the
    // canonical petri-net-json examples — the ONLY coupling, project D5).
    fs: { allow: ["../.."] },
  },
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
  },
  // Declare web-worker as external so rollup (dev mode) doesn't try to bundle it.
  // elkjs v0.12.0 requires 'web-worker' which isn't available in all environments.
  // The empty shim in src/empty-web-worker.ts satisfies the import.
  // Note: vite 5.4 handles rollup config via @vitejs/plugin-react internally;
  // we use resolve.alias for esbuild (build) and the shim path for dev fallback.
  resolve: {
    alias: {
      "web-worker": path.resolve(__dirname, "src/empty-web-worker.ts"),
    },
  },
  // For rollup external declaration (dev mode Vite uses rollup under the hood)
  // we set it via the Vite env - but simpler: just keep the alias approach.
});