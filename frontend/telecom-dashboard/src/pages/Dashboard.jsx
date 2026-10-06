import { useEffect, useMemo, useState } from 'react'
import Topbar from '../components/Topbar.jsx'
import StatCard from '../components/StatCard.jsx'
import Panel from '../components/Panel.jsx'
import ChurnRateChart from '../components/ChurnRateChart.jsx'
import DistributionChart from '../components/DistributionChart.jsx'
import SignalBars from '../components/SignalBars.jsx'
import { getAgeDistribution, getChurnRate, getDistribution, getGenderDistribution, getRiskDistribution } from '../api/analytics.js'
import AgeDistributionChart from '../components/AgeDistributionChart.jsx'
import GenderBreakdownChart from '../components/GenderBreakdownChart.jsx'
import RiskDistributionChart from '../components/RiskDistributionChart.jsx'
import './Dashboard.css'

export default function Dashboard() {
  const [churnRates, setChurnRates] = useState(null)
  const [distribution, setDistribution] = useState(null)
  const [ageData, setAgeData] = useState(null)
  const [genderData, setGenderData] = useState(null)
  const [riskData, setRiskData] = useState(null)
  const [error, setError] = useState('')
 

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        // Age/gender breakdowns are aggregated server-side (GET
        // /analytics/age-distribution, /analytics/gender-distribution) so we
        // only ever pull a handful of bucketed rows, not the full customer
        // table, no matter how large the dataset gets.
        const [rates, dist, age, gender, risk] = await Promise.all([
          getChurnRate(),
          getDistribution(),
          getAgeDistribution(),
          getGenderDistribution(),
          getRiskDistribution(),
        ])
        if (!cancelled) {
          setChurnRates(rates)
          setDistribution(dist)
          setAgeData(age)
          setGenderData(gender)
          setRiskData(risk)
        }
      } catch (err) {
        // Log the real cause instead of swallowing it - check the console/network
        // tab to see which endpoint failed and why (401, CORS, 404, network error, etc).
        console.error('Analytics load failed:', err)
        if (!cancelled) {
          const status = err.response?.status
          const detail = err.response?.data?.detail
          if (status === 401) {
            setError('Not authorized — your session may have expired. Try logging in again.')
          } else if (!err.response) {
            setError('Could not reach the backend. Is it running, and is CORS enabled for this origin?')
          } else {
            setError(detail || `Could not load analytics (status ${status ?? 'unknown'}).`)
          }
        }
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  const stats = useMemo(() => {
    if (!churnRates || !distribution) return null

    const partnerCounts = distribution.partners
    let weightedChurn = 0
    let weightTotal = 0
    let riskiest = null

    for (const row of churnRates) {
      const count = partnerCounts[row.telecom_partner] || 0
      weightedChurn += (row.churn_rate / 100) * count
      weightTotal += count
      if (!riskiest || row.churn_rate > riskiest.churn_rate) riskiest = row
    }

    return {
      overallChurn: weightTotal ? (weightedChurn / weightTotal) * 100 : 0,
      riskiest,
    }
  }, [churnRates, distribution])

  const loading = !churnRates || !distribution

  return (
    <div>
      <Topbar title="Dashboard" subtitle="Churn and coverage across your telecom partners" />

      {error && <p className="dashboard__state">{error}</p>}

      {!error && loading && (
        <div className="dashboard__state">
          <SignalBars variant="loading" label="Loading" />
          <span>Reading the network…</span>
        </div>
      )}

      {!error && !loading && (
        <>
          <div className="dashboard__stats">
            <StatCard label="Total customers" value={distribution.total_customers.toLocaleString()} />
            <StatCard
              label="Overall churn rate"
              value={`${stats.overallChurn.toFixed(1)}%`}
              tone={stats.overallChurn >= 25 ? 'bad' : 'good'}
            />
            <StatCard label="Partners tracked" value={Object.keys(distribution.partners).length} tone="accent" />
            <StatCard
              label="Highest churn partner"
              value={stats.riskiest?.telecom_partner ?? '—'}
              hint={stats.riskiest ? `${stats.riskiest.churn_rate.toFixed(1)}% churn` : undefined}
              tone="bad"
            />
          </div>

          <div className="dashboard__charts">
            <Panel title="Churn rate by partner" subtitle="Share of customers marked as churned">
              <ChurnRateChart data={churnRates} />
            </Panel>
            <Panel title="Customer distribution" subtitle="Customers per telecom partner">
              <DistributionChart partners={distribution.partners} />
            </Panel>
            <Panel title="Age distribution" subtitle="Customers by age bracket">
              <AgeDistributionChart data={ageData} />
            </Panel>
            <Panel title="Gender by partner" subtitle="Male vs. female customers per partner">
              <GenderBreakdownChart data={genderData} />
            </Panel>
            <Panel title="Risk distribution" subtitle="Risk Distribution based on Customer_id"> 
              <RiskDistributionChart data={riskData}/></Panel>
          </div>
        </>
      )}
    </div>
  )
}
