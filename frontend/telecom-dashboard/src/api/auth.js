import { apiClient, setToken, clearToken } from './client'

/**
 * ASSUMPTION: your auth.py wasn't included with the routes you shared, so this
 * assumes the common FastAPI pattern of an OAuth2PasswordRequestForm login at
 * POST /auth/token, form-encoded (not JSON), returning { access_token, token_type }.
 *
 * If your actual login route differs (different path, JSON body, different
 * response shape), this is the only file you need to edit.
 */
export async function login(username, password) {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)

  const { data } = await apiClient.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

  setToken(data.access_token)
  return data
}

export function logout() {
  clearToken()
}
