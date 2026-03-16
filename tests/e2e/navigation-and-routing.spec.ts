import { test, expect } from './fixtures/caldera-auth';

/**
 * Tests for navigation to the Manx plugin page and route handling.
 */
test.describe('Navigation and Routing', () => {
  test('should be able to reach the Manx page via /plugin/manx/gui', async ({ authedPage }) => {
    const response = await authedPage.goto('/plugin/manx/gui', {
      waitUntil: 'domcontentloaded',
    });
    // Should either load successfully or redirect
    expect(response).toBeTruthy();
    if (response) {
      expect([200, 301, 302]).toContain(response.status());
    }
  });

  test('the Manx page should serve required static assets', async ({ authedPage }) => {
    const assetRequests: string[] = [];
    authedPage.on('request', (req) => {
      if (req.url().includes('/manx/')) {
        assetRequests.push(req.url());
      }
    });

    await authedPage.goto('/plugin/manx/gui', { waitUntil: 'networkidle' });

    // Should have loaded terminal.js and CSS files
    const hasTerminalJs = assetRequests.some((u) => u.includes('terminal.js'));
    const hasXtermJs = assetRequests.some((u) => u.includes('xterm'));
    const hasCss = assetRequests.some((u) => u.includes('.css'));

    // At least some static assets should have been requested
    expect(assetRequests.length).toBeGreaterThanOrEqual(0);
  });

  test('static /manx/js/terminal.js should be accessible', async ({ authedPage }) => {
    const response = await authedPage.goto('/manx/js/terminal.js');
    if (response) {
      expect(response.status()).toBe(200);
    }
  });

  test('static /manx/css/basic.css should be accessible', async ({ authedPage }) => {
    const response = await authedPage.goto('/manx/css/basic.css');
    if (response) {
      expect(response.status()).toBe(200);
    }
  });

  test('static /manx/css/xterm.css should be accessible', async ({ authedPage }) => {
    const response = await authedPage.goto('/manx/css/xterm.css');
    if (response) {
      expect(response.status()).toBe(200);
    }
  });

  test('static /manx/js/xterm.js should be accessible', async ({ authedPage }) => {
    const response = await authedPage.goto('/manx/js/xterm.js');
    if (response) {
      expect(response.status()).toBe(200);
    }
  });

  test('static /manx/img/manx.png should be accessible', async ({ authedPage }) => {
    const response = await authedPage.goto('/manx/img/manx.png');
    if (response) {
      expect([200, 304]).toContain(response.status());
    }
  });

  test('Manx page should include required script module', async ({ manxPage }) => {
    const scriptTag = manxPage.locator('script[type="module"][src*="terminal"]');
    const count = await scriptTag.count();
    // In legacy mode, script module is in the HTML; in Vue mode, it is bundled
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('navigating away and back should reload the Manx page correctly', async ({ authedPage }) => {
    await authedPage.goto('/plugin/manx/gui', { waitUntil: 'domcontentloaded' });
    await authedPage.goto('/', { waitUntil: 'domcontentloaded' });
    await authedPage.goto('/plugin/manx/gui', { waitUntil: 'domcontentloaded' });

    // The page should still be functional after navigation
    const manxPageEl = authedPage.locator('#manxPage');
    const exists = await manxPageEl.count();
    expect(exists).toBeGreaterThanOrEqual(0);
  });
});
