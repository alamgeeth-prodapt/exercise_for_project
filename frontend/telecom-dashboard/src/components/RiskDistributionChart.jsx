import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

function categoryColor(name) {
  const c = name.toLowerCase()
  if (c.includes('low')) return 'var(--signal-good)'
  if (c.includes('high')) return 'var(--signal-bad)'
  return 'var(--accent)' // medium, or anything else
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip__label">{name} risk</p>
      <p className="chart-tooltip__value mono">{value.toLocaleString()} customers</p>
    </div>
  )
}

// `data` is [{ risk_category, count }] from GET /analytics/risk-distribution
export default function RiskDistributionChart({ data }) {
  const chartData = data.map((row) => ({ name: row.risk_category, value: row.count }))

  return (
    <div className="distribution-chart">
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius={64}
            outerRadius={96}
            paddingAngle={2}
            strokeWidth={0}
          >
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={categoryColor(entry.name)} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      <ul className="distribution-chart__legend">
        {chartData.map((entry) => (
          <li key={entry.name}>
            <span
              className="distribution-chart__swatch"
              style={{ background: categoryColor(entry.name) }}
            />
            <span className="distribution-chart__legend-name">{entry.name}</span>
            <span className="distribution-chart__legend-value mono">{entry.value.toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}