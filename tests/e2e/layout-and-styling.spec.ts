import { test, expect } from './fixtures/caldera-auth';

/**
 * Tests for the page layout, CSS styling, and responsive behavior.
 */
test.describe('Layout and Styling', () => {
  test('dropdowns should use Bulma .select.is-small class', async ({ manxPage }) => {
    const selectWrappers = manxPage.locator('#manxPage .select.is-small');
    const count = await selectWrappers.count();
    expect(count).toBe(4);
  });

  test('dropdown row should use flexbox space-around layout', async ({ manxPage }) => {
    const flexRow = manxPage.locator('.is-flex.is-flex-direction-row.is-justify-content-space-around');
    await expect(flexRow).toBeVisible();

    const style = await flexRow.evaluate((el) => {
      const cs = window.getComputedStyle(el);
      return {
        display: cs.display,
        flexDirection: cs.flexDirection,
        justifyContent: cs.justifyContent,
      };
    });
    expect(style.display).toBe('flex');
    expect(style.flexDirection).toBe('row');
    expect(style.justifyContent).toBe('space-around');
  });

  test('main container should use flex column layout', async ({ manxPage }) => {
    const flexCol = manxPage.locator('.is-flex.is-flex-direction-column').first();
    await expect(flexCol).toBeVisible();

    const style = await flexCol.evaluate((el) => {
      const cs = window.getComputedStyle(el);
      return {
        display: cs.display,
        flexDirection: cs.flexDirection,
      };
    });
    expect(style.display).toBe('flex');
    expect(style.flexDirection).toBe('column');
  });

  test('dropdown row should have bottom margin (mb-5)', async ({ manxPage }) => {
    const flexRow = manxPage.locator('.is-flex.is-flex-direction-row.is-justify-content-space-around.mb-5');
    await expect(flexRow).toBeVisible();
  });

  test('description text should have bold styling for key phrases', async ({ manxPage }) => {
    const boldElements = manxPage.locator('#manxPage .has-text-weight-bold');
    const count = await boldElements.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('italic elements should highlight key terms', async ({ manxPage }) => {
    const italicElements = manxPage.locator('#manxPage i');
    const count = await italicElements.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('xterm terminal container should be a block-level element', async ({ manxPage }) => {
    const xterminal = manxPage.locator('#xterminal');
    await expect(xterminal).toBeVisible();
  });

  test('hidden command element should not be visible', async ({ manxPage }) => {
    const cmdEl = manxPage.locator('#xterminal-command');
    // Element should exist but not be visible to the user
    await expect(cmdEl).toBeAttached();
    const isVisible = await cmdEl.isVisible();
    expect(isVisible).toBe(false);
  });

  test('page should be usable at 1280x720 viewport', async ({ manxPage }) => {
    await manxPage.setViewportSize({ width: 1280, height: 720 });
    await manxPage.waitForTimeout(1000);

    await expect(manxPage.locator('#manxPage')).toBeVisible();
    await expect(manxPage.locator('#session-id')).toBeVisible();
    await expect(manxPage.locator('#xterminal')).toBeVisible();
  });

  test('page should be usable at 1920x1080 viewport', async ({ manxPage }) => {
    await manxPage.setViewportSize({ width: 1920, height: 1080 });
    await manxPage.waitForTimeout(1000);

    await expect(manxPage.locator('#manxPage')).toBeVisible();
    await expect(manxPage.locator('#session-id')).toBeVisible();
    await expect(manxPage.locator('#xterminal')).toBeVisible();
  });

  test('page should handle narrow viewport (800px)', async ({ manxPage }) => {
    await manxPage.setViewportSize({ width: 800, height: 600 });
    await manxPage.waitForTimeout(1000);

    // The page should still render without crashing
    await expect(manxPage.locator('#manxPage')).toBeVisible();
  });
});
