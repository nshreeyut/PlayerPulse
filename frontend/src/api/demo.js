/**
 * Demo API
 * All calls go to /api/v1/demo/* — completely separate from real player routes.
 * Every response includes _demo: true from the backend.
 */
import client from './client';

export async function fetchDemoSummary() {
  const { data } = await client.get('/api/v1/demo/summary');
  return data;
}

export async function fetchDemoPlayers({ platform, limit = 20 } = {}) {
  const params = { limit };
  if (platform) params.platform = platform;
  const { data } = await client.get('/api/v1/demo/players', { params });
  return data;
}

export async function fetchDemoPlayer(playerId) {
  const { data } = await client.get(`/api/v1/demo/players/${playerId}`);
  return data;
}

/**
 * Stream a chat message in demo mode.
 * Uses native fetch (not axios) because axios buffers streaming responses.
 *
 * @param {object} opts
 * @param {string}   opts.message
 * @param {string}   [opts.playerId]
 * @param {Array}    [opts.conversationHistory]
 * @param {Function} opts.onChunk   — called with each text chunk as it arrives
 * @param {Function} opts.onDone    — called when stream ends
 * @param {Function} opts.onError   — called on error
 */
export async function streamDemoChat({
  message,
  playerId = null,
  conversationHistory = [],
  onChunk,
  onDone,
  onError,
}) {
  try {
    const baseUrl = import.meta.env.VITE_API_URL || '';
    const res = await fetch(`${baseUrl}/api/v1/demo/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        player_id: playerId,
        conversation_history: conversationHistory,
      }),
    });

    if (!res.ok) {
      throw new Error(`Demo chat error: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      onChunk(chunk);
    }

    onDone();
  } catch (err) {
    onError(err);
  }
}

/** Pre-defined demo player IDs. */
export const DEMO_PLAYER_IDS = Array.from({ length: 50 }, (_, i) => ({
  id: `Player_${i + 1}`,
  label: `Player_${i + 1}`,
}));
