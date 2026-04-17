/**
 * Studios API — registration, API key management, account settings.
 *
 * TODO (Sprint 6):
 *   - registerStudio(name, email) → { studio_id, api_key }
 *   - getStudio() → Studio profile (key masked)
 */

import client from './client'

/**
 * Register a new studio account.
 * Returns the API key — shown once, must be copied immediately.
 *
 * TODO (Sprint 6): implement
 */
export async function registerStudio({ name, email }) {
  throw new Error('TODO (Sprint 6): implement registerStudio')
  // const { data } = await client.post('/api/v1/studios', { name, email })
  // return data  // { studio_id, api_key, message }
}

/**
 * Fetch the current studio's profile.
 * Requires X-API-Key header (set in client interceptor).
 *
 * TODO (Sprint 6): implement
 */
export async function getStudio() {
  throw new Error('TODO (Sprint 6): implement getStudio')
  // const { data } = await client.get('/api/v1/studios/me')
  // return data
}
