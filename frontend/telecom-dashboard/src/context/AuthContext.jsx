import { createContext, useContext, useMemo, useState } from 'react'
import { login as loginRequest, logout as logoutRequest } from '../api/auth'
import { getToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(getToken())

  const value = useMemo(
    () => ({
      isAuthenticated: Boolean(token),
      async login(username, password) {
        const data = await loginRequest(username, password)
        setTokenState(data.access_token)
      },
      logout() {
        logoutRequest()
        setTokenState(null)
      },
    }),
    [token],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
