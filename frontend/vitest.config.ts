import { defineConfig } from "vitest/config"

export default defineConfig({
    test: {
        include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
        clearMocks: true,
        restoreMocks: true,
        unstubGlobals: true,
    },
})
