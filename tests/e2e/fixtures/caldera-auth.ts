import { test as base, expect, Page } from '@playwright/test';

/**
 * Shared fixtures that handle Caldera authentication and navigation to the
 * Manx plugin page.  Caldera's default credentials (admin/admin) are used
 * unless overridden via environment variables.
 */

export const CALDERA_USER = process.env.CALDERA_USER || 'admin';
export const CALDERA_PASS = process.env.CALDERA_PASS || 'admin';

/** Authenticate against Caldera and return an authenticated page. */
async function authenticateCaldera(page: Page): Promise<void> {
  const baseURL = page.context().browser()?.contexts()[0]?.pages()[0]?.url() || '';
  // Attempt to visit the home page; Caldera will redirect to login if not authed.
  await page.goto('/', { waitUntil: 'domcontentloaded' });

  // Caldera may present a login form. Fill it if present.
  const loginForm = page.locator('form').first();
  const usernameField = page.locator('input[name="username"], input[type="text"]').first();

  if (await usernameField.isVisible({ timeout: 5_000 }).catch(() => false)) {
    await usernameField.fill(CALDERA_USER);
    const passwordField = page.locator('input[name="password"], input[type="password"]').first();
    await passwordField.fill(CALDERA_PASS);
    await page.locator('button[type="submit"], input[type="submit"]').first().click();
    await page.waitForURL('**/*', { waitUntil: 'domcontentloaded' });
  }
}

/** Navigate to the Manx plugin page. Works for both legacy and magma UIs. */
async function navigateToManx(page: Page): Promise<void> {
  // Legacy (Jinja) route
  const legacyUrl = '/plugin/manx/gui';
  // Magma (Vue SPA) route - manx is loaded inside the plugins section
  const magmaUrl = '/#/plugins/manx';

  // Try legacy first
  const response = await page.goto(legacyUrl, { waitUntil: 'domcontentloaded' });
  if (response && response.status() === 200) {
    return;
  }

  // Fall back to magma SPA route
  await page.goto(magmaUrl, { waitUntil: 'domcontentloaded' });
}

export type ManxFixtures = {
  /** An authenticated page already on the Manx plugin page. */
  manxPage: Page;
  /** An authenticated page at the Caldera home (for navigation tests). */
  authedPage: Page;
};

export const test = base.extend<ManxFixtures>({
  authedPage: async ({ page }, use) => {
    await authenticateCaldera(page);
    await use(page);
  },

  manxPage: async ({ page }, use) => {
    await authenticateCaldera(page);
    await navigateToManx(page);
    await use(page);
  },
});

export { expect };
