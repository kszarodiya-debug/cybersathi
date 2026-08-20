import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

import { AuthContext, type AuthContextValue } from '../auth/context'
import { ChatPage } from './ChatPage'

const student = {
  id: 1,
  name: 'Campus Student',
  email: 'student@example.edu',
  role: 'student' as const,
  department: 'Computer Science',
  year: 2,
  created_at: '2026-08-19T00:00:00Z',
  updated_at: '2026-08-19T00:00:00Z',
}

describe('CyberSathi chat page', () => {
  it('loads history and sends a suggested question through the authenticated API', async () => {
    const authenticatedRequest = vi.fn()
      .mockResolvedValueOnce({ messages: [] })
      .mockResolvedValueOnce({
        id: 7,
        message: 'What is phishing?',
        response: 'Phishing is a deceptive attempt to steal information.',
        created_at: '2026-08-20T10:00:00Z',
      })
    const authValue = {
      user: student,
      accessToken: 'test-token',
      isAuthenticated: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      authenticatedRequest,
    } as unknown as AuthContextValue

    render(<AuthContext.Provider value={authValue}><MemoryRouter><ChatPage /></MemoryRouter></AuthContext.Provider>)

    await waitFor(() => expect(authenticatedRequest).toHaveBeenCalledWith('/chat/history'))
    await userEvent.click(screen.getByRole('button', { name: 'What is phishing?' }))
    await userEvent.click(screen.getByRole('button', { name: 'Send question' }))

    await waitFor(() => expect(screen.getByText('Phishing is a deceptive attempt to steal information.')).toBeInTheDocument())
    expect(authenticatedRequest).toHaveBeenLastCalledWith('/chat', {
      method: 'POST',
      body: JSON.stringify({ message: 'What is phishing?' }),
    })
  })
})
