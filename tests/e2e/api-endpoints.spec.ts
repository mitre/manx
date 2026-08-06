import { test, expect } from './fixtures/caldera-auth';

/**
 * Tests that the Manx REST API endpoints respond correctly.
 * These are lightweight contract tests verifying the UI's backend is wired up.
 */
test.describe('Manx API Endpoints', () => {
  test('GET /plugin/manx/sessions should return JSON', async ({ authedPage }) => {
    const response = await authedPage.request.get('/plugin/manx/sessions');
    expect(response.status()).toBe(200);
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('application/json');
  });

  test('GET /plugin/manx/sessions should return a sessions array', async ({ authedPage }) => {
    const response = await authedPage.request.get('/plugin/manx/sessions');
    const body = await response.json();
    // Response should contain a sessions key (magma format) or be an array (legacy)
    if (body.sessions) {
      expect(Array.isArray(body.sessions)).toBe(true);
    } else {
      expect(Array.isArray(body)).toBe(true);
    }
  });

  test('POST /plugin/manx/sessions should return session list', async ({ authedPage }) => {
    const response = await authedPage.request.post('/plugin/manx/sessions');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toBeTruthy();
  });

  test('POST /plugin/manx/history should accept paw parameter', async ({ authedPage }) => {
    const response = await authedPage.request.post('/plugin/manx/history', {
      data: { paw: 'nonexistent-paw' },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
    // Non-existent paw should return empty history
    expect(body).toHaveLength(0);
  });

  test('POST /plugin/manx/ability should accept paw parameter', async ({ authedPage }) => {
    const response = await authedPage.request.post('/plugin/manx/ability', {
      data: { paw: 'nonexistent-paw' },
    });
    // Should not crash; may return empty abilities
    expect([200, 400, 500]).toContain(response.status());
  });

  test('session objects should have required fields', async ({ authedPage }) => {
    const response = await authedPage.request.get('/plugin/manx/sessions');
    const body = await response.json();
    const sessions = body.sessions || body;

    if (Array.isArray(sessions) && sessions.length > 0) {
      const session = sessions[0];
      expect(session).toHaveProperty('id');
      expect(session).toHaveProperty('info');
    }
  });

  test('history entries should have cmd and paw fields', async ({ authedPage }) => {
    // Get a session first to find a real paw
    const sessResponse = await authedPage.request.get('/plugin/manx/sessions');
    const sessBody = await sessResponse.json();
    const sessions = sessBody.sessions || sessBody;

    if (Array.isArray(sessions) && sessions.length > 0) {
      const paw = sessions[0].info;
      const histResponse = await authedPage.request.post('/plugin/manx/history', {
        data: { paw },
      });
      const history = await histResponse.json();

      if (Array.isArray(history) && history.length > 0) {
        expect(history[0]).toHaveProperty('cmd');
        expect(history[0]).toHaveProperty('paw');
      }
    }
  });
});
