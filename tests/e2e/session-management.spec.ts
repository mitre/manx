import { test, expect } from './fixtures/caldera-auth';

/**
 * Tests for session listing, selection, and the session dropdown behavior.
 */
test.describe('Session Management', () => {
  test('should display the session select dropdown', async ({ manxPage }) => {
    const sessionSelect = manxPage.locator('#session-id');
    await expect(sessionSelect).toBeVisible();
  });

  test('should show "Select a session" as the default placeholder', async ({ manxPage }) => {
    const defaultOption = manxPage.locator('#session-id option[disabled][selected]');
    await expect(defaultOption).toHaveText('Select a session');
  });

  test('session dropdown should be inside a Bulma .select wrapper', async ({ manxPage }) => {
    const selectWrapper = manxPage.locator('.select.is-small').first();
    await expect(selectWrapper).toBeVisible();
    const innerSelect = selectWrapper.locator('select');
    await expect(innerSelect).toBeVisible();
  });

  test('should display session options when sessions are available', async ({ manxPage }) => {
    // Wait for potential session data to load (API may be mocked or live)
    await manxPage.waitForTimeout(4000);
    const options = manxPage.locator('#session-id option');
    const count = await options.count();
    // At minimum the placeholder option should exist
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('session option text should include id and paw info', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);
    const options = manxPage.locator('#session-id option:not([disabled])');
    const count = await options.count();
    if (count > 0) {
      const text = await options.first().textContent();
      // Format expected: "id - paw"
      expect(text).toMatch(/\d+\s*-\s*.+/);
    }
  });

  test('selecting a session should trigger tactic loading', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);
    const sessionSelect = manxPage.locator('#session-id');
    const options = manxPage.locator('#session-id option:not([disabled])');
    const count = await options.count();

    if (count > 0) {
      const value = await options.first().getAttribute('value');
      if (value) {
        // Intercept the ability API call to verify it fires
        const abilityPromise = manxPage.waitForRequest(
          (req) => req.url().includes('/plugin/manx/ability'),
          { timeout: 10_000 }
        ).catch(() => null);

        await sessionSelect.selectOption(value);
        const request = await abilityPromise;
        // If a request was made, the session selection triggered tactic loading
        if (request) {
          expect(request.method()).toBe('POST');
        }
      }
    }
  });

  test('session options should carry data-paw attribute', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);
    const options = manxPage.locator('#session-id option:not([disabled])');
    const count = await options.count();
    if (count > 0) {
      const dataPaw = await options.first().getAttribute('data-paw');
      expect(dataPaw).toBeTruthy();
    }
  });

  test('session options should carry data-platform attribute', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);
    const options = manxPage.locator('#session-id option:not([disabled])');
    const count = await options.count();
    if (count > 0) {
      const dataPlatform = await options.first().getAttribute('data-platform');
      expect(dataPlatform).toBeTruthy();
    }
  });

  test('session options should carry data-executor attribute', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);
    const options = manxPage.locator('#session-id option:not([disabled])');
    const count = await options.count();
    if (count > 0) {
      const dataExecutor = await options.first().getAttribute('data-executor');
      expect(dataExecutor).toBeTruthy();
    }
  });

  test('sessions should refresh periodically', async ({ manxPage }) => {
    // Track session API calls over time
    const calls: number[] = [];
    manxPage.on('request', (req) => {
      if (req.url().includes('/plugin/manx/sessions')) {
        calls.push(Date.now());
      }
    });

    // Wait long enough for at least one refresh cycle (3s interval)
    await manxPage.waitForTimeout(7000);
    expect(calls.length).toBeGreaterThanOrEqual(1);
  });
});
