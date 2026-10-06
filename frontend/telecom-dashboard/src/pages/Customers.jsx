import { useEffect, useState } from 'react'
import Topbar from '../components/Topbar.jsx'
import Panel from '../components/Panel.jsx'
import FilterBar, { emptyFilters } from '../components/FilterBar.jsx'
import CustomerTable from '../components/CustomerTable.jsx'
import Pagination from '../components/Pagination.jsx'
import SignalBars from '../components/SignalBars.jsx'
import { getCustomers } from '../api/customers.js'
import { predictChurn } from '../api/prediction.js'
import { exportCustomers } from '../api/customers.js'

const PAGE_SIZE = 20

export default function Customers() {
  const [filters, setFilters] = useState(emptyFilters)
  const [page, setPage] = useState(1)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [predictions, setPredictions] = useState({})

  useEffect(() => {
    let cancelled = false
    setLoading(true)

    async function load() {
      try {
        const data = await getCustomers({
          page,
          page_size: PAGE_SIZE,
          partner: filters.partner,
          state: filters.state,
          city: filters.city,
          gender: filters.gender,
          churn: filters.churn,
          risk_category: filters.risk_category,
          age_min: filters.age_min,
          age_max: filters.age_max,
          search_id: filters.search_id,
        })
        if (!cancelled) {
          setResult(data)
          setError('')
        }
      } catch {
        if (!cancelled) setError('Could not load customers. Is the API running?')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [filters, page])

  function handleFilterChange(next) {
    setFilters(next)
    setPage(1)
  }

  function handleReset() {
    setFilters(emptyFilters)
    setPage(1)
  }

  async function handlePredict(customerId) {
    setPredictions((prev) => ({ ...prev, [customerId]: { loading: true } }))
    try {
      const { prediction } = await predictChurn(customerId)
      setPredictions((prev) => ({ ...prev, [customerId]: { value: prediction } }))
    } catch (err) {
      setPredictions((prev) => ({ ...prev, [customerId]: { error: true, message: err.message } }))
    }
  }

  async function handleExport() {
  const blob = await exportCustomers({
    partner: filters.partner,
    state: filters.state,
    city: filters.city,
    gender: filters.gender,
    churn: filters.churn,
    age_min: filters.age_min,
    age_max: filters.age_max,
    search_id: filters.search_id,
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'customers.xlsx'
  link.click()
  URL.revokeObjectURL(url)
}

  return (
    <div>
      <Topbar title="Customers" subtitle="Browse, filter, and predict churn risk per customer" />
 
      <Panel title="Customer records">
        <div className="customer-table__toolbar">
          <FilterBar filters={filters} onChange={handleFilterChange} onReset={handleReset} />
          <button type="button" className="filter-bar__reset" onClick={handleExport}>
            Export Excel
          </button>
        </div>
 
        {error && <p className="customer-table__empty">{error}</p>}
 
        {!error && loading && (
          <div className="dashboard__state">
            <SignalBars variant="loading" label="Loading" />
            <span>Pulling customer records…</span>
          </div>
        )}
 
        {!error && !loading && result && (
          <>
            <CustomerTable customers={result.customers} predictions={predictions} onPredict={handlePredict} />
            <Pagination page={result.page} totalPages={result.total_pages} total={result.total} onChange={setPage} />
          </>
        )}
      </Panel>
    </div>
  )
}