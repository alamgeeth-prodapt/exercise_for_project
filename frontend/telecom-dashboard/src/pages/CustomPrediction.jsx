import { useState } from 'react'
import Topbar from '../components/Topbar.jsx'
import Panel from '../components/Panel.jsx'
import SignalBars from '../components/SignalBars.jsx'
import { predictCustom } from '../api/prediction.js'
import './CustomPrediction.css'

// NOTE: field names/types here assume CustomPredictionRequest mirrors the
// columns used everywhere else in this app. Rename/adjust to match your
// actual Pydantic model if it differs.
const todayISO = () => new Date().toISOString().slice(0, 10)

const initialForm = {
  telecom_partner: 'Airtel',
  gender: 'M',
  age: 30,
  state: '',
  city: '',
  num_dependents: 0,
  estimated_salary: 50000,
  calls_made: 20,
  sms_sent: 10,
  data_used: 5,
  date_of_registration: todayISO(),
}

const PARTNERS = ['Airtel', 'Jio', 'Vodafone Idea', 'BSNL']
const NUMERIC_FIELDS = new Set([
  'age',
  'num_dependents',
  'estimated_salary',
  'calls_made',
  'sms_sent',
  'data_used',
])

export default function CustomPrediction() {
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function update(field, value) {
    setForm((prev) => ({
      ...prev,
      [field]: NUMERIC_FIELDS.has(field) ? Number(value) : value,
    }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await predictCustom(form)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Topbar title="Custom Prediction" subtitle="Run churn prediction on hypothetical customer values" />

      <div className="custom-prediction">
        <Panel title="Customer profile">
          <form className="custom-prediction__form" onSubmit={handleSubmit}>
            <label className="cp-field">
              <span>Telecom partner</span>
              <select value={form.telecom_partner} onChange={(e) => update('telecom_partner', e.target.value)}>
                {PARTNERS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </label>

            <label className="cp-field">
              <span>Gender</span>
              <select value={form.gender} onChange={(e) => update('gender', e.target.value)}>
                <option value="M">Male</option>
                <option value="F">Female</option>
              </select>
            </label>

            <label className="cp-field">
              <span>Age</span>
              <input type="number" min="0" value={form.age} onChange={(e) => update('age', e.target.value)} required />
            </label>

            <label className="cp-field">
              <span>State</span>
              <input type="text" value={form.state} onChange={(e) => update('state', e.target.value)} placeholder="Tamil Nadu" required />
            </label>

            <label className="cp-field">
              <span>City</span>
              <input type="text" value={form.city} onChange={(e) => update('city', e.target.value)} placeholder="Chennai" required />
            </label>

            <label className="cp-field">
              <span>Registered on</span>
              <input
                type="date"
                value={form.date_of_registration}
                onChange={(e) => update('date_of_registration', e.target.value)}
                required
              />
            </label>

            <label className="cp-field">
              <span>Dependents</span>
              <input type="number" min="0" value={form.num_dependents} onChange={(e) => update('num_dependents', e.target.value)} />
            </label>

            <label className="cp-field">
              <span>Estimated salary</span>
              <input type="number" min="0" value={form.estimated_salary} onChange={(e) => update('estimated_salary', e.target.value)} />
            </label>

            <label className="cp-field">
              <span>Calls made</span>
              <input type="number" min="0" value={form.calls_made} onChange={(e) => update('calls_made', e.target.value)} />
            </label>

            <label className="cp-field">
              <span>SMS sent</span>
              <input type="number" min="0" value={form.sms_sent} onChange={(e) => update('sms_sent', e.target.value)} />
            </label>

            <label className="cp-field">
              <span>Data used (MB)</span>
              <input type="number" min="0" step="0.1" value={form.data_used} onChange={(e) => update('data_used', e.target.value)} />
            </label>

            <button type="submit" className="cp-submit" disabled={loading}>
              {loading ? 'Predicting…' : 'Run prediction'}
            </button>
          </form>
        </Panel>

        <Panel title="Result">
          {loading && (
            <div className="dashboard__state">
              <SignalBars variant="loading" label="Predicting" />
              <span>Scoring this profile…</span>
            </div>
          )}

          {!loading && error && <p className="cp-error">{error}</p>}

          {!loading && !error && !result && (
            <p className="cp-empty">Fill in the profile and run a prediction to see the result here.</p>
          )}

          {!loading && result && (
            <div className={`cp-result ${result.prediction ? 'cp-result--bad' : 'cp-result--good'}`}>
              <SignalBars
                variant="meter"
                strength={result.prediction ? 1 : 4}
                label="Predicted retention"
              />
              <div className="cp-result__text">
                <strong>{result.prediction ? 'Likely to churn' : 'Likely to stay'}</strong>
                <span>{(result.probability * 100).toFixed(1)}% churn probability</span>
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  )
}