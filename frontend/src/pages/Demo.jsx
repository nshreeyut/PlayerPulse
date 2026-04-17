import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import DemoBanner from '../components/DemoBanner/DemoBanner'
import AnalyticsPanel from '../components/AnalyticsPanel/AnalyticsPanel'
import FleetOverview from '../components/FleetOverview/FleetOverview'
import ChatPanel from '../components/ChatPanel/ChatPanel'
import { fetchDemoPlayers, fetchDemoPlayer, fetchDemoSummary, streamDemoChat } from '../api/demo'
import './Demo.css'

const FLEET_QUESTIONS = [
  "What's the overall churn rate across all players?",
  "Which player segment is most at risk right now?",
  "What are the top churn drivers across the player base?",
  "What retention actions should we prioritize this week?",
]

const FEATURE_KEYS = [
  'games_7d', 'games_14d', 'games_30d',
  'playtime_7d_hours', 'playtime_14d_hours', 'playtime_30d_hours',
  'avg_daily_sessions_7d', 'avg_daily_sessions_14d', 'avg_daily_sessions_30d',
  'max_gap_days_30d', 'games_trend_7d_vs_14d', 'playtime_trend_7d_vs_14d',
  'win_rate_7d', 'win_rate_30d', 'rating_change_30d',
  'unique_peers_30d', 'peer_games_30d', 'engagement_score', 'days_since_last_game',
]

function adaptPlayer(raw) {
  if (!raw) return null
  const features = {}
  FEATURE_KEYS.forEach(k => { features[k] = raw[k] })
  return {
    player_id: raw.player_id,
    platform: raw.platform,
    features,
    prediction: {
      churn_probability: raw.churn_probability,
      churn_predicted: raw.churn_predicted,
      risk_level: raw.risk_level,
      model_used: raw.model_used,
    },
    shap_values: raw.shap_values,
    _demo: true,
  }
}

const RISK_COLOR = { High: '#e05c5c', Medium: '#f5a623', Low: '#5cb85c' }
const PLATFORM_LABEL = { opendota: 'Dota', steam: 'Steam' }
const RISK_LEVELS = ['All', 'High', 'Medium', 'Low']

function Demo() {
  const navigate = useNavigate()
  const [playerList, setPlayerList] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [player, setPlayer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [view, setView] = useState('fleet')
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('All')

  useEffect(() => {
    fetchDemoSummary().then(setSummary).catch(() => {})
  }, [])

  useEffect(() => {
    fetchDemoPlayers({ limit: 50 })
      .then(data => {
        setPlayerList(data.players)
        if (data.players.length > 0) setSelectedId(data.players[0].player_id)
      })
      .catch(err => console.error('Failed to load demo players:', err))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    setLoading(true)
    setError(null)
    fetchDemoPlayer(selectedId)
      .then(raw => setPlayer(adaptPlayer(raw)))
      .catch(() => setError('Failed to load player data.'))
      .finally(() => setLoading(false))
  }, [selectedId])

  const filteredPlayers = useMemo(() => {
    return playerList.filter(p => {
      const matchesSearch = p.player_id.toLowerCase().includes(search.toLowerCase())
      const matchesRisk = riskFilter === 'All' || p.risk_level === riskFilter
      return matchesSearch && matchesRisk
    })
  }, [playerList, search, riskFilter])

  // Count by risk level for filter pill badges
  const riskCounts = useMemo(() => {
    const counts = { High: 0, Medium: 0, Low: 0 }
    playerList.forEach(p => { if (counts[p.risk_level] != null) counts[p.risk_level]++ })
    return counts
  }, [playerList])

  function demoStreamFn({ message, playerContext, conversationHistory, onChunk, onDone, onError }) {
    return streamDemoChat({ message, playerId: selectedId, conversationHistory, onChunk, onDone, onError })
  }

  return (
    <div className="demo-page">
      <DemoBanner onExit={() => navigate('/')} />

      {summary && (
        <div className="fleet-summary">
          <div className="fleet-stat">
            <span className="fleet-stat-value">{summary.total_players}</span>
            <span className="fleet-stat-label">Total Players</span>
          </div>
          <div className="fleet-stat-divider" />
          <div className="fleet-stat">
            <span className="fleet-stat-value" style={{ color: '#e05c5c' }}>
              {(summary.churn_rate * 100).toFixed(0)}%
            </span>
            <span className="fleet-stat-label">Churn Rate</span>
          </div>
          <div className="fleet-stat-divider" />
          <div className="fleet-stat">
            <span className="fleet-stat-value" style={{ color: '#e05c5c' }}>{summary.high_risk_count}</span>
            <span className="fleet-stat-label">High Risk</span>
          </div>
          <div className="fleet-stat-divider" />
          <div className="fleet-stat">
            <span className="fleet-stat-value" style={{ color: '#f5a623' }}>{summary.medium_risk_count}</span>
            <span className="fleet-stat-label">Medium Risk</span>
          </div>
          <div className="fleet-stat-divider" />
          <div className="fleet-stat">
            <span className="fleet-stat-value" style={{ color: '#5cb85c' }}>{summary.low_risk_count}</span>
            <span className="fleet-stat-label">Low Risk</span>
          </div>
          <div className="fleet-stat-divider" />
          <div className="fleet-stat">
            <span className="fleet-stat-value">{(summary.avg_churn_probability * 100).toFixed(0)}%</span>
            <span className="fleet-stat-label">Avg Churn Prob</span>
          </div>
        </div>
      )}

      <div className="demo-layout">
        {/* ── Sidebar ── */}
        <aside className="demo-sidebar">
          <div className="sidebar-search-wrap">
            <span className="search-icon">⌕</span>
            <input
              className="sidebar-search"
              type="text"
              placeholder="Search players…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && (
              <button className="search-clear" onClick={() => setSearch('')}>✕</button>
            )}
          </div>

          <div className="risk-filters">
            {RISK_LEVELS.map(level => (
              <button
                key={level}
                className={`risk-pill ${riskFilter === level ? 'active' : ''} ${level !== 'All' ? `risk-pill-${level.toLowerCase()}` : ''}`}
                onClick={() => setRiskFilter(level)}
              >
                {level}
                {level !== 'All' && (
                  <span className="risk-pill-count">{riskCounts[level]}</span>
                )}
              </button>
            ))}
          </div>

          <div className="sidebar-list-header">
            <span>Player</span>
            <span>Risk</span>
          </div>

          <ul className="player-list">
            {filteredPlayers.length === 0 ? (
              <li className="player-list-empty">No players match</li>
            ) : filteredPlayers.map(p => (
              <li
                key={p.player_id}
                className={`player-item ${selectedId === p.player_id ? 'active' : ''}`}
                onClick={() => { setSelectedId(p.player_id); setView('player') }}
              >
                <span className="risk-dot" style={{ background: RISK_COLOR[p.risk_level] }} />
                <div className="player-item-info">
                  <span className="player-item-id">{p.player_id}</span>
                  <span className="player-item-platform">{PLATFORM_LABEL[p.platform] ?? p.platform}</span>
                </div>
                <span className="player-item-prob" style={{ color: RISK_COLOR[p.risk_level] }}>
                  {(p.churn_probability * 100).toFixed(0)}%
                </span>
              </li>
            ))}
          </ul>

          <div className="sidebar-footer">
            {filteredPlayers.length} of {playerList.length} players
          </div>
        </aside>

        {/* ── Main ── */}
        <main className="demo-main">
          <div className="view-tabs">
            <button
              className={`view-tab ${view === 'fleet' ? 'active' : ''}`}
              onClick={() => setView('fleet')}
            >
              Fleet Overview
            </button>
            <button
              className={`view-tab ${view === 'player' ? 'active' : ''}`}
              onClick={() => setView('player')}
            >
              Player Analysis
              {selectedId && view === 'player' && (
                <span className="view-tab-id">{selectedId}</span>
              )}
            </button>
          </div>

          <div className="demo-content">
            <div className="demo-analytics">
              {view === 'fleet'
                ? <FleetOverview summary={summary} playerList={playerList} />
                : <AnalyticsPanel player={player} loading={loading} error={error} />
              }
            </div>
            <div className="demo-chat">
              <ChatPanel
                key={view === 'fleet' ? 'fleet-chat' : selectedId}
                playerContext={view === 'player' ? player : null}
                streamFn={demoStreamFn}
                suggestedQuestions={FLEET_QUESTIONS}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default Demo
