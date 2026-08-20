import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AuthProvider } from './AuthContext'
import { useAuth } from './useAuth'

function AuthHarness() {
  const { user, login } = useAuth()

  return (
    <>
      <button type="button" onClick={() => void login('student@example.edu', 'StrongPassword!123')}>
        Sign in
      </button>
      <span>{user?.name ?? 'Signed out'}</span>
    </>
  )
}

describe('authentication state', () => {
  it('keeps the authenticated user in memory and omits credentials by default', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: 'test-access-token',
          token_type: 'bearer',
          expires_in: 900,
          user: {
            id: 1,
            name: 'Campus Student',
            email: 'student@example.edu',
            role: 'student',
            department: null,
            year: 2,
            created_at: '2026-08-19T00:00:00Z',
            updated_at: '2026-08-19T00:00:00Z',
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => expect(screen.getByText('Campus Student')).toBeInTheDocument())

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/auth/login'),
      expect.objectContaining({ credentials: 'omit' }),
    )
  })
})
