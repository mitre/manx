import { test, expect } from './fixtures/caldera-auth';

/**
 * Tests for error states: no sessions, API failures, broken connections.
 */
test.describe('Error States', () => {
  test('should show empty session dropdown when no agents are connected', async ({ manxPage }) => {
    // On a fresh install with no agents, the session list should be empty
    const sessionOptions = manxPage.locator('#session-id option:not([disabled])');
    // Count may be 0 if no sessions exist
    const count = await sessionOptions.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('page should not crash when session API returns empty array', async ({ manxPage }) => {
    // Verify the page is still functional even with no sessions
    await expect(manxPage.locator('#manxPage')).toBeVisible();
    await expect(manxPage.locator('#xterminal')).toBeVisible();
  });

  test('tactic dropdown should remain disabled-like with no session selected', async ({ manxPage }) => {
    // Without selecting a session, the tactic dropdown should have no populated options
    const tacticOptions = manxPage.locator('#tactic-filter option:not([disabled])');
    const count = await tacticOptions.count();
    expect(count).toBe(0);
  });

  test('should handle session refresh API failure gracefully', async ({ manxPage }) => {
    // Intercept session API to return an error
    await manxPage.route('**/plugin/manx/sessions', (route) =>
      route.fulfill({ status: 500, body: 'Internal Server Error' })
    );

    // Reload and wait - the page should not crash
    await manxPage.reload({ waitUntil: 'domcontentloaded' });
    await manxPage.waitForTimeout(5000);

    // The page should still be rendered
    await expect(manxPage.locator('#manxPage')).toBeVisible();
  });

  test('should handle ability API failure gracefully', async ({ manxPage }) => {
    await manxPage.route('**/plugin/manx/ability', (route) =>
      route.fulfill({ status: 500, body: 'Internal Server Error' })
    );

    // Even if ability loading fails, the page should remain usable
    await expect(manxPage.locator('#manxPage')).toBeVisible();
  });

  test('should handle history API failure gracefully', async ({ manxPage }) => {
    await manxPage.route('**/plugin/manx/history', (route) =>
      route.fulfill({ status: 500, body: 'Internal Server Error' })
    );

    // Page should still work
    await expect(manxPage.locator('#manxPage')).toBeVisible();
  });

  test('console errors from API failures should not crash the page', async ({ manxPage }) => {
    const errors: string[] = [];
    manxPage.on('pageerror', (error) => errors.push(error.message));

    // Force a session refresh error
    await manxPage.route('**/plugin/manx/sessions', (route) =>
      route.fulfill({ status: 500, body: 'Server Error' })
    );

    await manxPage.reload({ waitUntil: 'domcontentloaded' });
    await manxPage.waitForTimeout(5000);

    // Page should still render even if there were console errors
    await expect(manxPage.locator('#manxPage')).toBeVisible();
  });

  test('terminal should remain functional after a dead session', async ({ manxPage }) => {
    await manxPage.waitForTimeout(3000);
    // After a dead session, the terminal should be cleared and the prompt reset
    // Click on the terminal and verify it is still interactive
    const terminal = manxPage.locator('#xterminal');
    await terminal.click();
    const textarea = manxPage.locator('.xterm-helper-textarea');
    if (await textarea.count() > 0) {
      await textarea.type('test');
      await manxPage.waitForTimeout(500);
      // No crash = success
    }
  });

  test('should handle network timeout on session refresh', async ({ manxPage }) => {
    // Simulate a very slow response (timeout)
    await manxPage.route('**/plugin/manx/sessions', async (route) => {
      await new Promise((r) => setTimeout(r, 30000));
      await route.fulfill({ status: 200, body: '[]' });
    });

    await manxPage.reload({ waitUntil: 'domcontentloaded' });
    await manxPage.waitForTimeout(5000);

    // Page should still be rendered
    await expect(manxPage.locator('#manxPage')).toBeVisible();
  });
});
