import { defineConfig } from "@playwright/test";

const apiUrl = "http://127.0.0.1:8010";
const webUrl = "http://127.0.0.1:3010";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  reporter: "list",
  use: {
    baseURL: webUrl,
    browserName: "chromium",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "npm run api:e2e",
      url: `${apiUrl}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        DATABASE_URL: "sqlite:///./cubeai-playwright.db",
        CORS_ORIGINS: '["http://127.0.0.1:3010"]',
        DEBUG: "false",
        HOST: "127.0.0.1",
        PORT: "8010",
      },
    },
    {
      command: "npm run web:e2e",
      url: webUrl,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        NEXT_PUBLIC_API_URL: apiUrl,
        NEXT_PUBLIC_WS_URL: "ws://127.0.0.1:8010",
        NEXT_DIST_DIR: ".next-e2e",
      },
    },
  ],
});