import { defineConfig } from "vitest/config";

/** Default config runs everything — unit + E2E. */
export default defineConfig({
  test: {
    globals: true,
    include: ["specs/**/*.test.ts"],
    testTimeout: 600_000,
    hookTimeout: 30_000,
    reporters: ["verbose"],
    pool: "threads",
    poolOptions: {
      threads: { maxThreads: 1 },
    },
  },
});
