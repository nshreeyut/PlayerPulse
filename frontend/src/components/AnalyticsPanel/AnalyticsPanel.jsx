/**
 * AnalyticsPanel Component
 * =========================
 * Displays all analytics for a looked-up player.
 * This is the left column of the home page.
 *
 * PROPS:
 *   player  — the full response from fetchPlayerAnalytics (or null if not loaded)
 *   loading — boolean, true while the API call is in flight
 *   error   — string error message, or null
 *
 * WHAT TO DISPLAY (build these in order — start simple, add detail):
 *
 * 1. LOADING STATE
 *    Show a spinner or skeleton while data is being fetched.
 *    CSS skeleton loaders are a good touch: https://css-tricks.com/building-skeleton-screens-css-custom-properties/
 *
 * 2. ERROR STATE
 *    Show a clear error message if the player wasn't found or the API failed.
 *    e.g., "Player 'xyz' not found on Chess.com. Check the spelling and try again."
 *
 * 3. PLAYER HEADER (once data is loaded)
 *    - Player ID and platform name
 *    - Risk level badge (color coded: green=Low, yellow=Medium, red=High)
 *
 * 4. PREDICTION CARD
 *    - Churn probability as a large number: "73%"
 *    - A simple progress bar or gauge showing the probability visually
 *    - "Churned" / "Active" label based on churn_predicted
 *
 * 5. KEY STATS GRID
 *    Show the most important features as labeled cards:
 *      - Engagement Score (0–100)
 *      - Days Since Last Game
 *      - Games in Last 7 Days
 *      - Win Rate (7 days)
 *    Use player.features to access these values.
 *
 * 6. SHAP CHART
 *    Import and render <ShapChart shapValues={player.shap_values} />
 *    This shows which features are driving the prediction.
 *
 * DATA SHAPE (what player looks like):
 *   player = {
 *     player_id: "hikaru",
 *     platform:  "chess_com",
 *     features:  { games_7d: 14, engagement_score: 72.3, days_since_last_game: 1, ... },
 *     prediction: { churn_probability: 0.18, churn_predicted: false, risk_level: "Low", model_used: "ensemble" },
 *     shap_values: [{ feature: "...", label: "...", shap_value: 0.42, direction: "increases_churn" }, ...]
 *   }
 *
 * TODO: Implement this component, section by section.
 */

import ShapChart from '../ShapChart/ShapChart'
import './AnalyticsPanel.css'

const RISK_COLORS = { High: '#e05c5c', Medium: '#f5a623', Low: '#5cb85c' }

const KEY_STATS = [
  { key: 'engagement_score',    label: 'Engagement Score',      fmt: v => v.toFixed(1) },
  { key: 'days_since_last_game', label: 'Days Since Last Game',  fmt: v => v },
  { key: 'games_7d',            label: 'Games (7 Days)',         fmt: v => v },
  { key: 'win_rate_7d',         label: 'Win Rate (7 Days)',      fmt: v => (v * 100).toFixed(0) + '%' },
]

function AnalyticsSkeleton() {
  return (
    <div className="analytics-panel">
      <div className="player-header">
        <div>
          <div className="skeleton skeleton-name" />
          <div className="skeleton skeleton-platform" />
        </div>
        <div className="skeleton skeleton-badge" />
      </div>
      <div className="prediction-card">
        <div className="skeleton skeleton-prob" />
        <div className="skeleton skeleton-label" />
        <div className="skeleton skeleton-bar" />
      </div>
      <div className="stats-grid">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="stat-card">
            <div className="skeleton skeleton-stat-val" />
            <div className="skeleton skeleton-stat-label" />
          </div>
        ))}
      </div>
      <div className="skeleton skeleton-chart" />
    </div>
  )
}

function AnalyticsPanel({ player, loading, error }) {
  if (loading) return <AnalyticsSkeleton />
  if (error)   return <div className="analytics-panel error">{error}</div>
  if (!player) return null

  const { features, prediction, shap_values, player_id, platform } = player
  const { churn_probability, churn_predicted, risk_level, model_used } = prediction
  const riskColor = RISK_COLORS[risk_level] || '#888'
  const pct = (churn_probability * 100).toFixed(1)

  return (
    <div className="analytics-panel">
      <div className="player-header">
        <div>
          <div className="player-name">{player_id}</div>
          <div className="player-platform">{platform}</div>
        </div>
        <span className="risk-badge" style={{ background: riskColor }}>{risk_level} Risk</span>
      </div>

      <div className="prediction-card">
        <div className="churn-prob">{pct}%</div>
        <div className="churn-label">Churn Probability</div>
        <div className="prob-bar">
          <div className="prob-fill" style={{ width: `${pct}%`, background: riskColor }} />
        </div>
        <div className="churn-status">{churn_predicted ? '⚠ Predicted to Churn' : '✓ Predicted Active'}</div>
        <div className="model-used">Model: {model_used}</div>
      </div>

      <div className="stats-grid">
        {KEY_STATS.map(({ key, label, fmt }) => (
          <div key={key} className="stat-card">
            <div className="stat-value">{features[key] != null ? fmt(features[key]) : '—'}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {shap_values && <ShapChart shapValues={shap_values} />}
    </div>
  )
}

export default AnalyticsPanel
