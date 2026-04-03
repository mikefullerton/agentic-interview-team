import { defineConfig } from "vitest/config";

/** E2E config — skill tests that invoke Claude. */
export default defineConfig({
  test: {
    globals: true,
    include: ["specs/*.test.ts"],
    exclude: ["specs/unit/**"],
    testTimeout: 1_860_000, // 31 minutes — build tests are the longest
    hookTimeout: 1_860_000, // 31 minutes — beforeAll runs the skill
    reporters: ["verbose"],
    pool: "threads",
    poolOptions: {
      threads: { maxThreads: 1 }, // serialize — one interview at a time
    },
  },
});
