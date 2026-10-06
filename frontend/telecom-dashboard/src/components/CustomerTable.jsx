import SignalBars from './SignalBars.jsx'
import './CustomerTable.css'

function ChurnBadge({ churn }) {
  return (
    <span className={`churn-badge ${churn ? 'churn-badge--bad' : 'churn-badge--good'}`}>
      {churn ? 'Churned' : 'Retained'}
    </span>
  )
}

function riskTone(category) {
  const c = category.toLowerCase()
  if (c.includes('low')) return 'good'
  if (c.includes('high')) return 'bad'
  return 'warn' // medium, or anything else
}

function RiskBadge({ category, churned }) {
  if (!category) {
    return churned ? (
      <span className="risk-badge risk-badge--na" title="Risk isn't calculated for churned customers">
        N/A
      </span>
    ) : (
      <span className="risk-badge risk-badge--unknown" title="Not yet scored">
        Pending
      </span>
    )
  }
  return <span className={`risk-badge risk-badge--${riskTone(category)}`}>{category}</span>
}

function PredictionCell({ customerId, alreadyChurned, prediction, onPredict }) {
  // The API rejects predictions for customers who've already churned - we
  // already know that from this row, so skip the round trip entirely.
  if (alreadyChurned) {
    return <span className="prediction-note">Already churned</span>
  }
  if (prediction?.loading) {
    return <SignalBars variant="loading" label="Predicting" />
  }
  if (prediction?.error) {
    return (
      <span className="prediction-error">
        <span className="prediction-error__message">{prediction.message || 'Prediction failed.'}</span>
        <button className="predict-btn predict-btn--retry" onClick={() => onPredict(customerId)}>
          Retry
        </button>
      </span>
    )
  }
  if (prediction && prediction.value !== undefined) {
    const willChurn = Boolean(prediction.value)
    return (
      <span className="prediction-result">
        <SignalBars variant="meter" strength={willChurn ? 1 : 4} label="Predicted retention" />
        {willChurn ? 'At risk' : 'Likely to stay'}
      </span>
    )
  }
  return (
    <button className="predict-btn" onClick={() => onPredict(customerId)}>
      Predict
    </button>
  )
}

export default function CustomerTable({ customers, predictions, onPredict }) {
  if (customers.length === 0) {
    return <p className="customer-table__empty">No customers match these filters.</p>
  }

  return (
    <div className="customer-table__scroll">
      <table className="customer-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Partner</th>
            <th>Gender</th>
            <th>Age</th>
            <th>Location</th>
            <th>Registered</th>
            <th>Dependents</th>
            <th>Salary</th>
            <th>Calls</th>
            <th>SMS</th>
            <th>Data (MB)</th>
            <th>Risk</th>
            <th>Status</th>
            <th>Prediction</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((c) => (
            <tr key={c.customer_id}>
              <td className="mono">{c.customer_id}</td>
              <td>{c.telecom_partner}</td>
              <td>{c.gender}</td>
              <td>{c.age}</td>
              <td>
                {c.city}, {c.state}
              </td>
              <td className="mono">{c.date_of_registration}</td>
              <td>{c.num_dependents}</td>
              <td className="mono">{Number(c.estimated_salary).toLocaleString()}</td>
              <td className="mono">{c.calls_made}</td>
              <td className="mono">{c.sms_sent}</td>
              <td className="mono">{c.data_used}</td>
              <td>
                <RiskBadge category={c.risk_category} churned={c.churn} />
              </td>
              <td>
                <ChurnBadge churn={c.churn} />
              </td>
              <td>
                <PredictionCell
                  customerId={c.customer_id}
                  alreadyChurned={c.churn}
                  prediction={predictions[c.customer_id]}
                  onPredict={onPredict}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}