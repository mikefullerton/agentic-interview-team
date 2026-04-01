import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    include: ["specs/**/*.test.ts"],
    testTimeout: 600_000, // 10 minutes — interview tests are long
    hookTimeout: 30_000,
    reporters: ["verbose"],
    pool: "threads",
    poolOptions: {
      threads: { maxThreads: 1 }, // serialize — one interview at a time
    },
  },
});
