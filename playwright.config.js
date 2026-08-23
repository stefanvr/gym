// playwright.config.js
// doc/tech-spec.md's testing strategy: deliberately thin, desktop + mobile smoke coverage —
// reserved for CSS-media-query and viewport wiring the unit layer (test/) structurally can't see.
// Requires Node >=20 (doc/environment.md).

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  use: {
    baseURL: "http://127.0.0.1:8080",
  },
  webServer: {
    command: "npm run gyms:generate && npx http-server . -p 8080 -c-1",
    url: "http://127.0.0.1:8080",
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: "Desktop Chrome", use: { ...devices["Desktop Chrome"] } },
    { name: "Mobile Chrome", use: { ...devices["Pixel 7"] } },
  ],
});
