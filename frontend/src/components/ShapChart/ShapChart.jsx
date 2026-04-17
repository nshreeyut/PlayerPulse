/**
 * ShapChart Component
 * ====================
 * Renders a horizontal bar chart of SHAP feature importance values.
 * Shows which features are pushing the model toward or away from predicting churn.
 *
 * PROPS:
 *   shapValues — array from the API:
 *     [
 *       { feature: "days_since_last_game", label: "Days since last game", shap_value: 0.42, direction: "increases_churn" },
 *       { feature: "games_7d",             label: "Games (7 days)",       shap_value: -0.18, direction: "decreases_churn" },
 *       ...
 *     ]
 *
 * WHY RECHARTS?
 * --------------
 * Recharts is the most "React-native" charting library — you build charts
 * with JSX components rather than imperative D3 code.
 * It's declarative, easy to customize, and works well with React state.
 *
 * WHAT TO BUILD:
 * ---------------
 * A horizontal BarChart where:
 *   - Y-axis = feature labels (the human-readable names)
 *   - X-axis = SHAP values (negative = decreases churn, positive = increases churn)
 *   - Bars colored by direction:
 *       increases_churn  → red   (#e05c5c)
 *       decreases_churn  → green (#5cb85c)
 *   - Reference line at x=0
 *   - Show top 8 features maximum (most impactful)
 *
 * RECHARTS QUICK REFERENCE:
 * --------------------------
 * import { BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, Cell, ResponsiveContainer } from 'recharts'
 *
 * <ResponsiveContainer width="100%" height={300}>
 *   <BarChart data={data} layout="vertical">
 *     <XAxis type="number" />
 *     <YAxis type="category" dataKey="label" width={200} />
 *     <Tooltip />
 *     <ReferenceLine x={0} stroke="#666" />
 *     <Bar dataKey="shap_value">
 *       {data.map((entry, i) => (
 *         <Cell key={i} fill={entry.direction === 'increases_churn' ? '#e05c5c' : '#5cb85c'} />
 *       ))}
 *     </Bar>
 *   </BarChart>
 * </ResponsiveContainer>
 *
 * LEARN MORE: https://recharts.org/en-US/api
 *
 * TODO: Implement this component.
 * Steps:
 *   1. Import the Recharts components you need
 *   2. Slice the top 8 features: shapValues.slice(0, 8)
 *   3. Render the BarChart as described above
 *   4. Add a title: "What's Driving This Prediction?"
 *   5. Add a small legend explaining red = increases risk, green = decreases risk
 */

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, Cell, ResponsiveContainer,
} from 'recharts'
import './ShapChart.css'

function ShapChart({ shapValues }) {
  if (!shapValues || shapValues.length === 0) {
    return <p className="shap-empty">No SHAP data available.</p>
  }

  const topFeatures = shapValues.slice(0, 8)

  return (
    <div className="shap-chart">
      <h3>What's Driving This Prediction?</h3>
      <div className="shap-legend">
        <span className="legend-item increases">Increases risk</span>
        <span className="legend-item decreases">Decreases risk</span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={topFeatures} layout="vertical" margin={{ left: 0, right: 20, top: 4, bottom: 4 }}>
          <XAxis type="number" tick={{ fontSize: 11, fill: '#888' }} />
          <YAxis type="category" dataKey="label" width={185} tick={{ fontSize: 11, fill: '#ccc' }} />
          <Tooltip
            formatter={(value) => [value.toFixed(4), 'SHAP value']}
            contentStyle={{ background: '#1a1d2e', border: '1px solid #3a3d5e', borderRadius: 6 }}
            labelStyle={{ color: '#ccc' }}
          />
          <ReferenceLine x={0} stroke="#555" />
          <Bar dataKey="shap_value" radius={[0, 3, 3, 0]}>
            {topFeatures.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.direction === 'increases_churn' ? '#e05c5c' : '#5cb85c'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default ShapChart
