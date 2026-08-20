export interface AuthUser {
  id: number
  name: string
  email: string
  role: 'student' | 'faculty' | 'admin'
  department: string | null
  year: number | null
  created_at: string
  updated_at: string
}

export interface AuthSession {
  accessToken: string
  user: AuthUser
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: AuthUser
}
