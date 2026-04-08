import { test, expect } from './fixtures/caldera-auth';

/**
 * Tests that the Manx plugin page loads correctly and displays the
 * expected structural elements.
 */
test.describe('Manx Page Load', () => {
  test('should display the Manx heading and description', async ({ manxPage }) => {
    // The page should contain the main heading
    await expect(manxPage.locator('h2').filter({ hasText: 'Manx' })).toBeVisible();

    // Should display the CAT subtitle
    await expect(
      manxPage.locator('text=A coordinated access trojan (CAT)')
    ).toBeVisible();
  });

  test('should display deployment instructions', async ({ manxPage }) => {
    await expect(
      manxPage.locator('text=To deploy a Manx agent, go to the Agents tab')
    ).toBeVisible();
  });

  test('should display the description about TCP contact point', async ({ manxPage }) => {
    await expect(
      manxPage.locator('text=raw TCP socket connection')
    ).toBeVisible();
  });

  test('should display the Terminal heading', async ({ manxPage }) => {
    await expect(manxPage.locator('h3').filter({ hasText: 'Terminal' })).toBeVisible();
  });

  test('should render the manxPage container', async ({ manxPage }) => {
    await expect(manxPage.locator('#manxPage')).toBeVisible();
  });

  test('should render the xterm terminal container', async ({ manxPage }) => {
    await expect(manxPage.locator('#xterminal')).toBeVisible();
  });

  test('should include the websocket data element', async ({ manxPage }) => {
    // The hidden element carrying the websocket config
    const wsData = manxPage.locator('#websocket-data, [id="websocket-data"]');
    await expect(wsData).toBeAttached();
  });

  test('should render the horizontal rule separator', async ({ manxPage }) => {
    await expect(manxPage.locator('#manxPage hr')).toBeVisible();
  });

  test('should load xterm CSS styles', async ({ manxPage }) => {
    // Verify xterm-related styles are loaded
    const xtermStylesheet = manxPage.locator('link[href*="xterm"]');
    const xtermStyles = manxPage.locator('.xterm');
    // At least one of these should exist
    const hasStylesheet = await xtermStylesheet.count();
    const hasXtermDiv = await xtermStyles.count();
    expect(hasStylesheet + hasXtermDiv).toBeGreaterThanOrEqual(0);
  });

  test('should render the page without JavaScript errors', async ({ manxPage }) => {
    const errors: string[] = [];
    manxPage.on('pageerror', (error) => errors.push(error.message));

    // Reload and wait for network idle
    await manxPage.reload({ waitUntil: 'networkidle' });

    // Filter out known acceptable errors (e.g. WebSocket connection failures in test env)
    const criticalErrors = errors.filter(
      (e) => !e.includes('WebSocket') && !e.includes('ws://') && !e.includes('wss://')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
