/**
 * usePlayer — Custom React Hook
 * ==============================
 * Manages all state and data fetching for a player lookup.
 *
 * Usage:
 *   const { player, loading, error, refetch } = usePlayer('opendota', '87278757')
 */

import { useState, useEffect } from 'react'
import { fetchPlayerAnalytics } from '../api/players'

/**
 * @param {string|null} platform  - e.g., "opendota" (null until user searches)
 * @param {string|null} playerId  - e.g., "87278757"
 * @param {string}      modelId   - which model to use for the prediction
 *
 * @returns {{
 *   player:  object|null,
 *   loading: boolean,
 *   error:   string|null,
 *   refetch: Function
 * }}
 */
export function usePlayer(platform, playerId, modelId = 'ensemble') {
  const [player, setPlayer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function fetchPlayer() {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchPlayerAnalytics(platform, playerId, modelId)
      setPlayer(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Player not found.')
      setPlayer(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!platform || !playerId) return
    fetchPlayer()
  }, [platform, playerId, modelId])

  return { player, loading, error, refetch: fetchPlayer }
}
