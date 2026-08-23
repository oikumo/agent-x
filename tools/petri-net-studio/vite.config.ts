/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

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
});
