/**
 * PlayerSearch Component
 * =======================
 * A form where users select a gaming platform and enter a player ID.
 * When submitted, calls onSearch(platform, playerId) to notify the parent.
 *
 * PROPS:
 *   onSearch(platform, playerId) — called when the form is submitted
 */

import { useState, useEffect } from 'react'
import { fetchSupportedGames } from '../../api/players'
import './PlayerSearch.css'

function PlayerSearch({ onSearch }) {
  const [platform, setPlatform] = useState('')
  const [playerId, setPlayerId] = useState('')
  const [games, setGames] = useState([])
  const [validationError, setValidationError] = useState('')

  useEffect(() => {
    fetchSupportedGames().then(setGames).catch(console.error)
  }, [])

  const selectedGame = games.find(g => g.id === platform)

  function handleSubmit(e) {
    e.preventDefault()
    if (!platform || !playerId.trim()) {
      setValidationError('Please select a platform and enter a player ID.')
      return
    }
    setValidationError('')
    onSearch(platform, playerId.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="player-search">
      <div className="search-row">
        <select
          value={platform}
          onChange={e => setPlatform(e.target.value)}
          className="search-select"
        >
          <option value="">Select platform...</option>
          {games.map(g => (
            <option key={g.id} value={g.id}>{g.display_name}</option>
          ))}
        </select>

        <input
          type="text"
          value={playerId}
          onChange={e => setPlayerId(e.target.value)}
          placeholder={selectedGame?.player_id_example || 'Player ID'}
          className="search-input"
        />

        <button type="submit" className="search-button">
          Look Up Player
        </button>
      </div>

      {validationError && (
        <p className="search-error">{validationError}</p>
      )}
    </form>
  )
}

export default PlayerSearch
