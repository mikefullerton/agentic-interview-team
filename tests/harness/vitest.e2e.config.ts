import { defineConfig } from "vitest/config";

/** E2E config — only interview tests that invoke Claude. */
export default defineConfig({
  test: {
    globals: true,
    include: ["specs/*.test.ts"],
    exclude: ["specs/unit/**"],
    testTimeout: 600_000, // 10 minutes — interviews are long
    hookTimeout: 660_000, // 11 minutes — beforeAll runs the interview
    reporters: ["verbose"],
    pool: "threads",
    poolOptions: {
      threads: { maxThreads: 1 }, // serialize — one interview at a time
    },
  },
});
