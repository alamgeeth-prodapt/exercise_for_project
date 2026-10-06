import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

const PALETTE = ['#2B3A67', '#E8A33D', '#3FA796', '#8C7BC9', '#D64550', '#4FA3D1']

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip__label">{name}</p>
      <p className="chart-tooltip__value mono">{value.toLocaleString()} customers</p>
    </div>
  )
}

export default function DistributionChart({ partners }) {
  const data = Object.entries(partners).map(([name, value]) => ({ name, value }))

  return (
    <div className="distribution-chart">
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={64}
            outerRadius={96}
            paddingAngle={2}
            strokeWidth={0}
          >
            {data.map((entry, i) => (
              <Cell key={entry.name} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      <ul className="distribution-chart__legend">
        {data.map((entry, i) => (
          <li key={entry.name}>
            <span className="distribution-chart__swatch" style={{ background: PALETTE[i % PALETTE.length] }} />
            <span className="distribution-chart__legend-name">{entry.name}</span>
            <span className="distribution-chart__legend-value mono">{entry.value.toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
