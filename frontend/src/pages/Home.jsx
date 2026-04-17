/**
 * Home Page
 * ==========
 * The main page — combines the search, analytics, and chat in one view.
 *
 * PAGE LAYOUT:
 * ┌──────────────────────────────────────────────────────┐
 * │                   PlayerSearch                        │  ← top: platform + player ID input
 * ├─────────────────────────────┬────────────────────────┤
 * │      AnalyticsPanel         │      ChatPanel          │
 * │      (left ~60%)            │      (right ~40%)       │
 * │                             │                         │
 * │  • Churn probability        │  • Message history      │
 * │  • Risk level badge         │  • Streaming response   │
 * │  • SHAP chart               │  • Text input + send    │
 * │  • Feature stats            │                         │
 * └─────────────────────────────┴────────────────────────┘
 *
 * WHY STATE LIVES HERE ("lifting state up"):
 * -------------------------------------------
 * The selected player data is needed by BOTH AnalyticsPanel AND ChatPanel.
 * The ChatPanel needs it to give the LLM context.
 * The AnalyticsPanel needs it to display the charts and scores.
 *
 * In React, when multiple sibling components share data, that data must
 * live in their closest common ancestor (this component) and be passed
 * down as props. This is called "lifting state up."
 *
 * LEARN MORE:
 *   Lifting state up:  https://react.dev/learn/sharing-state-between-components
 *   props:             https://react.dev/learn/passing-props-to-a-component
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import PlayerSearch from '../components/PlayerSearch/PlayerSearch'
import AnalyticsPanel from '../components/AnalyticsPanel/AnalyticsPanel'
import ChatPanel from '../components/ChatPanel/ChatPanel'
import { usePlayer } from '../hooks/usePlayer'
import './Home.css'

function Home() {
  // Tracks which player the user has searched for
  const [selectedPlatform, setSelectedPlatform] = useState(null)
  const [selectedPlayerId, setSelectedPlayerId] = useState(null)

  // usePlayer fetches analytics whenever platform or playerId changes
  const { player, loading, error } = usePlayer(selectedPlatform, selectedPlayerId)

  // Called by PlayerSearch when the user submits the form
  function handleSearch(platform, playerId) {
    setSelectedPlatform(platform)
    setSelectedPlayerId(playerId)
  }

  return (
    <div className="home-page">
      <header className="site-header">
        <div className="site-header-inner">
          <div className="site-logo">
            <span className="logo-pulse" />
            PlayerPulse
          </div>
          <Link to="/demo" className="header-demo-link">Live Demo →</Link>
        </div>
      </header>

      <div className="search-wrapper">
        <PlayerSearch onSearch={handleSearch} />
      </div>

      {!selectedPlayerId ? (
        <div className="empty-state">
          <div className="empty-glow" />
          <h1 className="empty-title">AI-Powered Churn Prediction</h1>
          <p className="empty-desc">
            Look up any player by platform and ID. Get churn probability, SHAP feature breakdown, and an AI analyst ready to explain the prediction.
          </p>
          <Link to="/demo" className="demo-link">Explore the Demo →</Link>
        </div>
      ) : (
        <div className="results-layout">
          <div className="analytics-column">
            <AnalyticsPanel player={player} loading={loading} error={error} />
          </div>
          <div className="chat-column">
            <ChatPanel playerContext={player} />
          </div>
        </div>
      )}
    </div>
  )
}

export default Home
