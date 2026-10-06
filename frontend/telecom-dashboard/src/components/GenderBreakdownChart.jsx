import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

// `data` is already grouped server-side by GET /analytics/gender-distribution:
// [{ partner: 'Airtel', M: 120, F: 98 }, ...] - no client-side grouping needed.
export default function GenderBreakdownChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" />
        <XAxis dataKey="partner" tick={{ fontSize: 12, fill: 'var(--ink-soft)' }} axisLine={{ stroke: 'var(--line)' }} tickLine={false} />
        <YAxis tick={{ fontSize: 12, fill: 'var(--ink-soft)' }} axisLine={false} tickLine={false} width={36} />
        <Tooltip cursor={{ fill: 'var(--canvas-tint)' }} />
        <Legend />
        <Bar dataKey="M" fill="var(--primary)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="F" fill="var(--accent)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}