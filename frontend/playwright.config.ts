import { defineConfig, devices } from "@playwright/test";

const frontendURL = process.env.E2E_FRONTEND_URL ?? "http://localhost:5173";
const apiURL = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: frontendURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: `VITE_API_BASE_URL=${apiURL} VITE_API_TIMEOUT_MS=10000 npm run dev -- --host localhost`,
    url: frontendURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
