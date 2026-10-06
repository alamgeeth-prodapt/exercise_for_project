import { apiClient } from './client'

// GET /analytics/churn-rate -> [{ telecom_partner, churn_rate }]
export async function getChurnRate() {
  const { data } = await apiClient.get('/analytics/churn-rate')
  return data
}

// GET /analytics/distribution -> { total_customers, partners: { [name]: count } }
export async function getDistribution() {
  const { data } = await apiClient.get('/analytics/distribution')
  return data
}


// GET /analytics/age-distribution
export async function getAgeDistribution() {
  const { data } = await apiClient.get('/analytics/age-distribution')
  return data
}

// GET /analytics/gender-distribution
export async function getGenderDistribution() {
  const { data } = await apiClient.get('/analytics/gender-distribution')
  return data
}

export async function getRiskDistribution() {
  const { data } = await apiClient.get('/analytics/risk-distribution')
  return data
}
