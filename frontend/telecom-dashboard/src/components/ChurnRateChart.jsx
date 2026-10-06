import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip__label">{label}</p>
      <p className="chart-tooltip__value mono">{payload[0].value.toFixed(1)}% churn</p>
    </div>
  )
}

export default function ChurnRateChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" />
        <XAxis
          dataKey="telecom_partner"
          tick={{ fontSize: 12, fill: 'var(--ink-soft)' }}
          axisLine={{ stroke: 'var(--line)' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 12, fill: 'var(--ink-soft)' }}
          axisLine={false}
          tickLine={false}
          unit="%"
          width={44}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--canvas-tint)' }} />
        <Bar dataKey="churn_rate" fill="var(--primary)" radius={[6, 6, 0, 0]} maxBarSize={48} />
      </BarChart>
    </ResponsiveContainer>
  )
}
