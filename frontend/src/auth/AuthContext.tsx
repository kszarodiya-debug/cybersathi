import { useCallback, useMemo, useState, type ReactNode } from 'react'

import { apiRequest } from '../services/api'
import { AuthContext, type AuthContextValue } from './context'
import type { AuthSession, TokenResponse } from './types'

export function AuthProvider({ children }: { children: ReactNode }) {
  // Access tokens intentionally live only in React memory; they are never persisted in web storage.
  const [session, setSession] = useState<AuthSession | null>(null)

  const applyTokenResponse = useCallback((response: TokenResponse) => {
    setSession({ accessToken: response.access_token, user: response.user })
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiRequest<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    applyTokenResponse(response)
    return response.user
  }, [applyTokenResponse])

  const register = useCallback(async (name: string, email: string, password: string, department?: string) => {
    const response = await apiRequest<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password, department: department || undefined }),
    })
    applyTokenResponse(response)
    return response.user
  }, [applyTokenResponse])

  const logout = useCallback(async () => {
    const token = session?.accessToken
    try {
      if (token) {
        await apiRequest('/auth/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        })
      }
    } finally {
      setSession(null)
    }
  }, [session?.accessToken])

  const authenticatedRequest = useCallback(async <T,>(path: string, init: RequestInit = {}) => {
    if (!session) throw new Error('Authentication is required.')

    const headers = new Headers(init.headers)
    headers.set('Authorization', `Bearer ${session.accessToken}`)
    try {
      return await apiRequest<T>(path, { ...init, headers })
    } catch (error) {
      if (error instanceof Error && 'status' in error && (error as { status?: number }).status === 401) {
        setSession(null)
      }
      throw error
    }
  }, [session])

  const value = useMemo<AuthContextValue>(() => ({
    user: session?.user ?? null,
    accessToken: session?.accessToken ?? null,
    isAuthenticated: session !== null,
    login,
    register,
    logout,
    authenticatedRequest,
  }), [authenticatedRequest, login, logout, register, session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
