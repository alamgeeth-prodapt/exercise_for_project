import './Panel.css'

export default function Panel({ title, subtitle, children, className = '' }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel__head">
        <h2 className="panel__title">{title}</h2>
        {subtitle && <p className="panel__subtitle">{subtitle}</p>}
      </div>
      {children}
    </section>
  )
}
