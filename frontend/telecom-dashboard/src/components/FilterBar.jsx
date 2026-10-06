import './FilterBar.css'

const emptyFilters = {
  partner: '',
  state: '',
  city: '',
  gender: '',
  churn: '',
  risk_category: '',
  age_min: '',
  age_max: '',
  search_id: '',
}

export { emptyFilters }

export default function FilterBar({ filters, onChange, onReset }) {
  function update(field, value) {
    onChange({ ...filters, [field]: value })
  }

  return (
    <div className="filter-bar">
      <input
        className="filter-bar__id"
        type="number"
        placeholder="Search by customer ID"
        value={filters.search_id}
        onChange={(e) => update('search_id', e.target.value)}
      />

      <input
        type="text"
        placeholder="Partner"
        value={filters.partner}
        onChange={(e) => update('partner', e.target.value)}
      />
      <input
        type="text"
        placeholder="State"
        value={filters.state}
        onChange={(e) => update('state', e.target.value)}
      />
      <input
        type="text"
        placeholder="City"
        value={filters.city}
        onChange={(e) => update('city', e.target.value)}
      />

      <select value={filters.gender} onChange={(e) => update('gender', e.target.value)}>
        <option value="">Any gender</option>
        <option value="M">Male</option>
        <option value="F">Female</option>
      </select>

      <select value={filters.churn} onChange={(e) => update('churn', e.target.value)}>
        <option value="">Any status</option>
        <option value="false">Retained</option>
        <option value="true">Churned</option>
      </select>

      <select value={filters.risk_category} onChange={(e) => update('risk_category', e.target.value)}>
        <option value="">Any risk</option>
        <option value="Low Risk">Low risk</option>
        <option value="Medium Risk">Medium risk</option>
        <option value="High Risk">High risk</option>
      </select>

      <input
        type="number"
        placeholder="Min age"
        value={filters.age_min}
        onChange={(e) => update('age_min', e.target.value)}
        className="filter-bar__age"
      />
      <input
        type="number"
        placeholder="Max age"
        value={filters.age_max}
        onChange={(e) => update('age_max', e.target.value)}
        className="filter-bar__age"
      />

      <button type="button" className="filter-bar__reset" onClick={onReset}>
        Clear filters
      </button>
    </div>
  )
}