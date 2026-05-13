import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "../tests/e2e",
  timeout: 30_000,
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:8000",
    trace: "on-first-retry",
  },
  webServer: {
    command: "uv run python manage.py runserver 0.0.0.0:8000 --noreload",
    url: "http://localhost:8000/healthz",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    cwd: "..",
  },
});
