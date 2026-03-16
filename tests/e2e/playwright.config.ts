import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Manx E2E tests.
 *
 * Prerequisites:
 *   - A running Caldera instance with the manx (and magma) plugins enabled.
 *   - Default Caldera address: http://localhost:8888
 *   - Override with CALDERA_URL env var if needed.
 */
export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.ts',
  fullyParallel: false,          // tests share server state; run serially
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 60_000,

  use: {
    baseURL: process.env.CALDERA_URL || 'http://localhost:8888',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
});
