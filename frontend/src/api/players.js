/**
 * Players API Module
 * ===================
 * All API calls related to players, games, and models live here.
 */

import client from './client'

/**
 * Fetch the list of supported gaming platforms.
 * Powers the platform dropdown in PlayerSearch — fetched dynamically
 * so adding a new game to the backend registry appears without a frontend deploy.
 *
 * Returns: [{ id: "opendota", display_name: "Dota 2 (OpenDota)", player_id_example: "87278757", ... }]
 */
export async function fetchSupportedGames() {
  const response = await client.get('/api/v1/players/games')
  return response.data
}

/**
 * Fetch all registered ML models.
 * Use this to populate a model selector.
 *
 * Returns: [{ id: "ensemble", display_name: "Soft-Voting Ensemble", description: "..." }]
 */
export async function fetchModels() {
  const response = await client.get('/api/v1/players/models')
  return response.data
}

/**
 * Fetch full analytics for one player. This is the main call.
 * Powers the entire AnalyticsPanel and provides context to the ChatPanel.
 *
 * @param {string} platform  - e.g., "opendota"
 * @param {string} playerId  - e.g., "87278757"
 * @param {string} modelId   - e.g., "ensemble" (optional)
 *
 * Returns:
 * {
 *   player_id:   "87278757",
 *   platform:    "opendota",
 *   features:    { games_7d: 14, engagement_score: 72.3, ... },
 *   prediction:  { churn_probability: 0.18, risk_level: "Low", ... },
 *   shap_values: [{ feature: "days_since_last_game", shap_value: -0.31, direction: "decreases_churn" }, ...]
 * }
 */
export async function fetchPlayerAnalytics(platform, playerId, modelId = 'ensemble') {
  // encodeURIComponent encodes '#' as '%23' so Riot IDs like "Name#TAG"
  // survive the URL path without being truncated at the fragment symbol.
  const response = await client.get(`/api/v1/players/${platform}/${encodeURIComponent(playerId)}`, {
    params: { model_id: modelId },
  })
  return response.data
}

/**
 * Browse players in the dataset. Optionally filter by platform.
 */
export async function fetchPlayers(platform = null, limit = 50) {
  const response = await client.get('/api/v1/players', {
    params: { platform, limit },
  })
  return response.data
}
