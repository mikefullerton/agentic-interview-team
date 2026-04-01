import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    include: ["specs/unit/**/*.test.ts"],
    testTimeout: 10_000, // 10 seconds — unit tests are fast
    reporters: ["verbose"],
  },
});
