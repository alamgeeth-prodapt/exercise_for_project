import { apiClient } from './client'

// GET /customer/ with pagination + filters -> CustomerPaginationResponse
export async function getCustomers(params) {
  // Strip empty/undefined filter values so we don't send blank query params.
  const cleaned = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== undefined && v !== null),
  )
  const { data } = await apiClient.get('/customer/', { params: cleaned })
  return data
}

// GET /customer/export -> CSV blob (needs auth header, so we fetch + download manually)
export async function exportCustomers(params) {
  const cleaned = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== undefined && v !== null),
  )
  const response = await apiClient.get('/customer/export', {
    params: cleaned,
    responseType: 'blob',
  })
  return response.data
}

// Pulls a large page for client-side aggregation (histograms, breakdowns).
// Fine for a few thousand rows; if your dataset grows a lot, this is the
// first thing to replace with a real backend aggregate endpoint.
export async function getAllCustomers() {
  const { data } = await apiClient.get('/customer/', {
    params: { page: 1, page_size: 243553 },
  })
  return data.customers
}