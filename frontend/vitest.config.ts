// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: false,          // explicit imports preferred
    environment: 'jsdom',     // or 'jsdom' for DOM testing
    include: ['src/**/*.test.ts'],
    coverage: {
      provider: 'v8',        // or 'istanbul'
    },
  },
})