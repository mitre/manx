import { Page, Route } from '@playwright/test';

/**
 * API mocking helpers for testing the Manx UI without a live Caldera backend.
 * These intercept the REST / API calls that the Manx page makes and return
 * controlled fixture data so we can test the UI in isolation.
 */

export interface MockSession {
  id: number;
  info: string;
  platform: string;
  executors: string[];
}

export interface MockAbility {
  ability_id: string;
  tactic: string;
  technique_id: string;
  technique_name: string;
  name: string;
  executors: { platform: string; name: string; command: string }[];
}

export const MOCK_SESSIONS: MockSession[] = [
  { id: 1, info: 'paw-abc123', platform: 'linux', executors: ['sh'] },
  { id: 2, info: 'paw-def456', platform: 'darwin', executors: ['sh'] },
  { id: 3, info: 'paw-ghi789', platform: 'windows', executors: ['psh'] },
];

export const MOCK_ABILITIES: MockAbility[] = [
  {
    ability_id: 'abil-001',
    tactic: 'discovery',
    technique_id: 'T1082',
    technique_name: 'System Information Discovery',
    name: 'Get System Info',
    executors: [
      { platform: 'linux', name: 'sh', command: 'uname -a' },
      { platform: 'darwin', name: 'sh', command: 'uname -a' },
      { platform: 'windows', name: 'psh', command: 'systeminfo' },
    ],
  },
  {
    ability_id: 'abil-002',
    tactic: 'discovery',
    technique_id: 'T1083',
    technique_name: 'File and Directory Discovery',
    name: 'List Files',
    executors: [
      { platform: 'linux', name: 'sh', command: 'ls -la' },
      { platform: 'darwin', name: 'sh', command: 'ls -la' },
      { platform: 'windows', name: 'psh', command: 'dir' },
    ],
  },
  {
    ability_id: 'abil-003',
    tactic: 'collection',
    technique_id: 'T1005',
    technique_name: 'Data from Local System',
    name: 'Read File',
    executors: [
      { platform: 'linux', name: 'sh', command: 'cat /etc/hostname' },
    ],
  },
  {
    ability_id: 'abil-004',
    tactic: 'execution',
    technique_id: 'T1059',
    technique_name: 'Command and Scripting Interpreter',
    name: 'Run Shell Command',
    executors: [
      { platform: 'linux', name: 'sh', command: 'echo hello' },
      { platform: 'windows', name: 'psh', command: 'Write-Output hello' },
    ],
  },
];

export const MOCK_HISTORY = [
  { cmd: 'whoami', paw: 'paw-abc123', date: '2025-01-01T00:00:00Z' },
  { cmd: 'ls -la', paw: 'paw-abc123', date: '2025-01-01T00:01:00Z' },
  { cmd: 'id', paw: 'paw-abc123', date: '2025-01-01T00:02:00Z' },
];

/**
 * Install API route mocks on the given page. This intercepts the Manx REST
 * endpoints so the UI can be tested without a running Caldera server.
 */
export async function installMockApi(page: Page, options?: {
  sessions?: MockSession[];
  abilities?: MockAbility[];
  history?: typeof MOCK_HISTORY;
  failSessions?: boolean;
}): Promise<void> {
  const sessions = options?.sessions ?? MOCK_SESSIONS;
  const abilities = options?.abilities ?? MOCK_ABILITIES;
  const history = options?.history ?? MOCK_HISTORY;
  const failSessions = options?.failSessions ?? false;

  // Mock GET /plugin/manx/sessions  (magma Vue UI)
  await page.route('**/plugin/manx/sessions', async (route: Route) => {
    if (failSessions) {
      await route.fulfill({ status: 500, body: 'Internal Server Error' });
      return;
    }
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions }),
      });
    } else {
      // POST variant (legacy)
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(sessions),
      });
    }
  });

  // Mock POST /plugin/manx/ability
  await page.route('**/plugin/manx/ability', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ abilities }),
    });
  });

  // Mock POST /plugin/manx/history
  await page.route('**/plugin/manx/history', async (route: Route) => {
    const postData = route.request().postDataJSON();
    const paw = postData?.paw;
    const filtered = history.filter((h) => h.paw === paw);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(filtered),
    });
  });

  // Mock POST /api/rest (ability detail lookup)
  await page.route('**/api/rest', async (route: Route) => {
    const postData = route.request().postDataJSON();
    if (postData?.index === 'abilities') {
      const matched = abilities.filter((a) => a.ability_id === postData.ability_id);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(matched),
      });
    } else {
      await route.continue();
    }
  });
}

/**
 * Install a mock WebSocket server-like interceptor. Since Playwright cannot
 * directly mock WebSocket connections, we provide a helper that intercepts
 * the page's WebSocket creation and tracks connection attempts.
 */
export async function trackWebSocketConnections(page: Page): Promise<string[]> {
  const wsUrls: string[] = [];

  page.on('websocket', (ws) => {
    wsUrls.push(ws.url());
  });

  return wsUrls;
}
