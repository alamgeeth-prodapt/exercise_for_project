import { apiClient } from './client'

// POST /prediction/{customer_id} -> { customer_id, prediction }
// The route now returns 404 if the customer doesn't exist and 400 if they've
// already churned, each with a `detail` message - surface that message as-is.
export async function predictChurn(customerId) {
  try {
    const { data } = await apiClient.post(`/prediction/${customerId}`)
    return data
  } catch (err) {
    const detail = err.response?.data?.detail
    throw new Error(detail || 'Prediction failed.')
  }
}

export async function predictCustom(payload) {
  try {
    const { data } = await apiClient.post('/prediction/custom', payload)
    return data
  } catch (err) {
    const detail = err.response?.data?.detail
    throw new Error(detail || 'Prediction Failed')
  }

}
