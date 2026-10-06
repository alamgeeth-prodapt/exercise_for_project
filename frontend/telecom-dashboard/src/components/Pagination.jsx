import './Pagination.css'

export default function Pagination({ page, totalPages, total, onChange }) {
  if (totalPages <= 0) return null

  return (
    <div className="pagination">
      <span className="pagination__summary mono">
        Page {page} of {totalPages} · {total.toLocaleString()} customers
      </span>
      <div className="pagination__controls">
        <button disabled={page <= 1} onClick={() => onChange(page - 1)}>
          ← Prev
        </button>
        <button disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
          Next →
        </button>
      </div>
    </div>
  )
}
