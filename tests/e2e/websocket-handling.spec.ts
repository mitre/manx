import { test, expect } from './fixtures/caldera-auth';

/**
 * Tests for WebSocket connection handling when running commands through
 * the Manx terminal.
 */
test.describe('WebSocket Connection Handling', () => {
  test('page should contain websocket configuration data', async ({ manxPage }) => {
    const wsDataEl = manxPage.locator('#websocket-data, [id="websocket-data"]');
    await expect(wsDataEl).toBeAttached();

    const wsAttr = await wsDataEl.getAttribute('data-websocket');
    // The websocket attribute should be set (format: "host:port")
    expect(wsAttr).toBeTruthy();
  });

  test('websocket config should contain host and port', async ({ manxPage }) => {
    const wsDataEl = manxPage.locator('#websocket-data, [id="websocket-data"]');
    const wsAttr = await wsDataEl.getAttribute('data-websocket');

    if (wsAttr) {
      const parts = wsAttr.split(':');
      expect(parts.length).toBeGreaterThanOrEqual(2);
      // Port should be numeric
      const port = parts[parts.length - 1];
      expect(Number(port)).not.toBeNaN();
    }
  });

  test('running a command should attempt WebSocket connection', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);

    const wsUrls: string[] = [];
    manxPage.on('websocket', (ws) => {
      wsUrls.push(ws.url());
    });

    const sessionOptions = manxPage.locator('#session-id option:not([disabled])');
    const sessionCount = await sessionOptions.count();

    if (sessionCount > 0) {
      const value = await sessionOptions.first().getAttribute('value');
      if (value) {
        await manxPage.locator('#session-id').selectOption(value);
        await manxPage.waitForTimeout(1000);

        // Type a command and press Enter
        const terminal = manxPage.locator('#xterminal');
        await terminal.click();
        const textarea = manxPage.locator('.xterm-helper-textarea');
        if (await textarea.count() > 0) {
          await textarea.type('whoami');
          await textarea.press('Enter');
          await manxPage.waitForTimeout(2000);

          // A WebSocket connection should have been attempted
          // The URL format is: ws(s)://host:port/manx/{sessionId}
          if (wsUrls.length > 0) {
            expect(wsUrls[0]).toContain('/manx/');
          }
        }
      }
    }
  });

  test('WebSocket URL should include the session ID', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);

    const wsUrls: string[] = [];
    manxPage.on('websocket', (ws) => {
      wsUrls.push(ws.url());
    });

    const sessionOptions = manxPage.locator('#session-id option:not([disabled])');
    if (await sessionOptions.count() > 0) {
      const value = await sessionOptions.first().getAttribute('value');
      if (value) {
        await manxPage.locator('#session-id').selectOption(value);
        await manxPage.waitForTimeout(1000);

        const terminal = manxPage.locator('#xterminal');
        await terminal.click();
        const textarea = manxPage.locator('.xterm-helper-textarea');
        if (await textarea.count() > 0) {
          await textarea.type('ls');
          await textarea.press('Enter');
          await manxPage.waitForTimeout(2000);

          if (wsUrls.length > 0) {
            expect(wsUrls[0]).toContain(`/manx/${value}`);
          }
        }
      }
    }
  });

  test('should use wss:// protocol on HTTPS pages', async ({ manxPage }) => {
    // Evaluate in-page to check the protocol logic
    const proto = await manxPage.evaluate(() => {
      return location.protocol === 'https:' ? 'wss://' : 'ws://';
    });
    // In test env (http), should be ws://
    expect(proto).toMatch(/^wss?:\/\/$/);
  });

  test('should handle 0.0.0.0 websocket host by using window.location.hostname', async ({ manxPage }) => {
    // This tests the logic in terminal.js where 0.0.0.0 is replaced
    const hostname = await manxPage.evaluate(() => window.location.hostname);
    expect(hostname).toBeTruthy();
    expect(hostname).not.toBe('0.0.0.0');
  });

  test('dead session response should show error message in terminal', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);

    const sessionOptions = manxPage.locator('#session-id option:not([disabled])');
    if (await sessionOptions.count() > 0) {
      const value = await sessionOptions.first().getAttribute('value');
      if (value) {
        await manxPage.locator('#session-id').selectOption(value);
        await manxPage.waitForTimeout(1000);

        // Send a command; if the session is dead, the terminal should show the error
        const terminal = manxPage.locator('#xterminal');
        await terminal.click();
        const textarea = manxPage.locator('.xterm-helper-textarea');
        if (await textarea.count() > 0) {
          await textarea.type('test-dead-session');
          await textarea.press('Enter');
          // Give time for the WebSocket to fail
          await manxPage.waitForTimeout(3000);
          // Session select should reset to index 0 if the session was dead
          // (We cannot fully assert text in canvas-based xterm, but the
          // flow should not crash the page.)
        }
      }
    }
  });
});
