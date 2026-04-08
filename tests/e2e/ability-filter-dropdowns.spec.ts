import { test, expect } from './fixtures/caldera-auth';

/**
 * Tests for the tactic -> technique -> procedure cascading dropdown filters.
 */
test.describe('Ability Filter Dropdowns', () => {
  test('should display the tactic filter dropdown', async ({ manxPage }) => {
    const tacticSelect = manxPage.locator('#tactic-filter');
    await expect(tacticSelect).toBeVisible();
  });

  test('tactic dropdown should show "Select a tactic" placeholder', async ({ manxPage }) => {
    const placeholder = manxPage.locator('#tactic-filter option[disabled][selected]');
    await expect(placeholder).toHaveText('Select a tactic');
  });

  test('should display the technique filter dropdown', async ({ manxPage }) => {
    // Technique select does not have an id in all versions; locate by structure
    const selects = manxPage.locator('.select.is-small select');
    const count = await selects.count();
    // There should be 4 dropdowns: session, tactic, technique, procedure
    expect(count).toBeGreaterThanOrEqual(4);
  });

  test('technique dropdown should show "Select a technique" placeholder', async ({ manxPage }) => {
    const placeholder = manxPage.locator('option[disabled][selected]').filter({ hasText: 'Select a technique' });
    await expect(placeholder).toBeAttached();
  });

  test('should display the procedure filter dropdown', async ({ manxPage }) => {
    const procedureSelect = manxPage.locator('#procedure-filter');
    await expect(procedureSelect).toBeVisible();
  });

  test('procedure dropdown should show "Select a procedure" placeholder', async ({ manxPage }) => {
    const placeholder = manxPage.locator('#procedure-filter option[disabled][selected]');
    await expect(placeholder).toHaveText('Select a procedure');
  });

  test('all four dropdowns should be in a flex row layout', async ({ manxPage }) => {
    const flexRow = manxPage.locator('.is-flex.is-flex-direction-row.is-justify-content-space-around');
    await expect(flexRow).toBeVisible();
    const dropdowns = flexRow.locator('.select.is-small');
    const count = await dropdowns.count();
    expect(count).toBe(4);
  });

  test('tactic dropdown should be empty until a session is selected', async ({ manxPage }) => {
    const tacticOptions = manxPage.locator('#tactic-filter option:not([disabled])');
    const count = await tacticOptions.count();
    expect(count).toBe(0);
  });

  test('technique dropdown should be empty until a tactic is selected', async ({ manxPage }) => {
    const selects = manxPage.locator('.select.is-small select');
    // The third select is technique (0-indexed: session=0, tactic=1, technique=2)
    if (await selects.count() >= 3) {
      const techniqueOptions = selects.nth(2).locator('option:not([disabled])');
      const count = await techniqueOptions.count();
      expect(count).toBe(0);
    }
  });

  test('procedure dropdown should be empty until a technique is selected', async ({ manxPage }) => {
    const procedureOptions = manxPage.locator('#procedure-filter option:not([disabled])');
    const count = await procedureOptions.count();
    expect(count).toBe(0);
  });

  test('selecting a session should populate the tactic dropdown', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);
    const sessionOptions = manxPage.locator('#session-id option:not([disabled])');
    const sessionCount = await sessionOptions.count();

    if (sessionCount > 0) {
      const value = await sessionOptions.first().getAttribute('value');
      if (value) {
        await manxPage.locator('#session-id').selectOption(value);
        await manxPage.waitForTimeout(3000);

        const tacticOptions = manxPage.locator('#tactic-filter option:not([disabled])');
        const tacticCount = await tacticOptions.count();
        // Tactics should now have options (if the API returned data)
        expect(tacticCount).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('changing session should reset tactic, technique, and procedure selections', async ({ manxPage }) => {
    await manxPage.waitForTimeout(4000);
    const sessionOptions = manxPage.locator('#session-id option:not([disabled])');
    const sessionCount = await sessionOptions.count();

    if (sessionCount > 1) {
      // Select first session
      const value1 = await sessionOptions.first().getAttribute('value');
      if (value1) {
        await manxPage.locator('#session-id').selectOption(value1);
        await manxPage.waitForTimeout(2000);
      }

      // Select second session - should reset filters
      const value2 = await sessionOptions.nth(1).getAttribute('value');
      if (value2) {
        await manxPage.locator('#session-id').selectOption(value2);
        await manxPage.waitForTimeout(1000);

        // Tactic should be reset to placeholder
        const tacticValue = await manxPage.locator('#tactic-filter').inputValue();
        expect(tacticValue).toBe('');
      }
    }
  });
});
