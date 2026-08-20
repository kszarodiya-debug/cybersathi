import { createContext } from 'react'

import type { AuthUser } from './types'

export interface AuthContextValue {
  user: AuthUser | null
  accessToken: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string, department?: string) => Promise<void>
  logout: () => Promise<void>
  authenticatedRequest: <T>(path: string, init?: RequestInit) => Promise<T>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
