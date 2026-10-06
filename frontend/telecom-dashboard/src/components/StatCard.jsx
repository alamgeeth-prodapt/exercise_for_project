import './StatCard.css'

export default function StatCard({ label, value, tone = 'neutral', hint }) {
  return (
    <div className={`stat-card stat-card--${tone}`}>
      <p className="stat-card__label">{label}</p>
      <p className="stat-card__value mono">{value}</p>
      {hint && <p className="stat-card__hint">{hint}</p>}
    </div>
  )
}
