import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  ScatterChart, Scatter, ZAxis, ReferenceLine,
} from 'recharts'
import './FleetOverview.css'

const RISK_COLORS = { High: '#e05c5c', Medium: '#f5a623', Low: '#5cb85c' }

const TOOLTIP_STYLE = {
  contentStyle: { background: '#181b2e', border: '1px solid #2a2d45', borderRadius: 6 },
  labelStyle: { color: '#dde1f0' },
  itemStyle: { color: '#9ba0c0' },
}

const AXIS_TICK = { fill: '#6b708f', fontSize: 11 }

function legendText(value) {
  return <span style={{ color: '#9ba0c0', fontSize: '0.75rem' }}>{value}</span>
}

function FleetOverview({ summary, playerList }) {
  if (!summary || !playerList.length) {
    return <div className="fleet-overview-loading">Loading fleet data…</div>
  }

  // ── Risk donut ────────────────────────────────────────────────
  const riskData = [
    { name: 'High',   value: summary.high_risk_count,   color: '#e05c5c' },
    { name: 'Medium', value: summary.medium_risk_count, color: '#f5a623' },
    { name: 'Low',    value: summary.low_risk_count,    color: '#5cb85c' },
  ]

  // ── Churn probability histogram ───────────────────────────────
  const histData = [
    { label: '0–20%',   min: 0,   max: 0.2  },
    { label: '20–40%',  min: 0.2, max: 0.4  },
    { label: '40–60%',  min: 0.4, max: 0.6  },
    { label: '60–80%',  min: 0.6, max: 0.8  },
    { label: '80–100%', min: 0.8, max: 1.01 },
  ].map(b => ({
    label:   b.label,
    players: playerList.filter(p => p.churn_probability >= b.min && p.churn_probability < b.max).length,
  }))

  // ── Engagement vs Churn scatter (split by risk for colours) ───
  const scatterByRisk = ['High', 'Medium', 'Low'].map(risk => ({
    risk,
    data: playerList
      .filter(p => p.risk_level === risk)
      .map(p => ({ engagement: Math.round(p.engagement_score), churn: Math.round(p.churn_probability * 100) })),
  }))

  // ── Platform risk stacked bar ─────────────────────────────────
  const platforms = [...new Set(playerList.map(p => p.platform))]
  const platformData = platforms.map(platform => {
    const group = playerList.filter(p => p.platform === platform)
    return {
      platform: platform === 'opendota' ? 'Dota 2' : 'Steam',
      High:   group.filter(p => p.risk_level === 'High').length,
      Medium: group.filter(p => p.risk_level === 'Medium').length,
      Low:    group.filter(p => p.risk_level === 'Low').length,
    }
  })

  return (
    <div className="fleet-overview">
      <div className="fleet-charts-grid">

        {/* Risk Distribution Donut */}
        <div className="chart-card">
          <p className="chart-title">Risk Distribution</p>
          <div className="chart-body">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={80}
                  dataKey="value"
                  paddingAngle={3}
                >
                  {riskData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip {...TOOLTIP_STYLE} />
                <Legend iconType="circle" iconSize={8} formatter={legendText} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Churn Probability Histogram */}
        <div className="chart-card">
          <p className="chart-title">Churn Probability Distribution</p>
          <div className="chart-body">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2235" vertical={false} />
                <XAxis dataKey="label" tick={AXIS_TICK} />
                <YAxis tick={AXIS_TICK} allowDecimals={false} />
                <Tooltip {...TOOLTIP_STYLE} />
                <Bar dataKey="players" name="Players" fill="#4f5bde" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Engagement Score vs Churn — full width */}
        <div className="chart-card chart-card--wide">
          <p className="chart-title">Engagement Score vs Churn Probability</p>
          <div className="chart-body">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2235" />
                <XAxis
                  type="number"
                  dataKey="engagement"
                  name="Engagement"
                  tick={AXIS_TICK}
                  label={{ value: 'Engagement Score', position: 'insideBottom', offset: -12, fill: '#424666', fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="churn"
                  name="Churn %"
                  tick={AXIS_TICK}
                  label={{ value: 'Churn %', angle: -90, position: 'insideLeft', offset: 10, fill: '#424666', fontSize: 11 }}
                />
                <ZAxis range={[35, 35]} />
                <ReferenceLine y={50} stroke="#2a2d45" strokeDasharray="4 4" />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  {...TOOLTIP_STYLE}
                  formatter={(v, name) => [v, name === 'engagement' ? 'Engagement Score' : 'Churn %']}
                />
                {scatterByRisk.map(({ risk, data }) => (
                  <Scatter
                    key={risk}
                    name={`${risk} Risk`}
                    data={data}
                    fill={RISK_COLORS[risk]}
                    fillOpacity={0.8}
                  />
                ))}
                <Legend iconType="circle" iconSize={8} formatter={legendText} verticalAlign="top" align="right" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Platform Risk Stacked Bar */}
        <div className="chart-card chart-card--wide">
          <p className="chart-title">Risk Breakdown by Platform</p>
          <div className="chart-body">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={platformData} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2235" horizontal={false} />
                <XAxis type="number" tick={AXIS_TICK} allowDecimals={false} />
                <YAxis type="category" dataKey="platform" tick={{ ...AXIS_TICK, fill: '#9ba0c0' }} width={55} />
                <Tooltip {...TOOLTIP_STYLE} />
              <Legend iconType="square" iconSize={8} formatter={legendText} />
              <Bar dataKey="High"   stackId="a" fill="#e05c5c" name="High Risk" />
              <Bar dataKey="Medium" stackId="a" fill="#f5a623" name="Medium Risk" />
              <Bar dataKey="Low"    stackId="a" fill="#5cb85c" name="Low Risk" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  )
}

export default FleetOverview
