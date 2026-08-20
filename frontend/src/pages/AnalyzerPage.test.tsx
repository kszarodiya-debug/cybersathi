import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

import { AuthContext, type AuthContextValue } from '../auth/context'
import { AnalyzerPage } from './AnalyzerPage'

describe('message analyzer page', () => {
  it('submits pasted message content and renders the backend risk result', async () => {
    const authenticatedRequest = vi.fn().mockResolvedValue({
      id: 12,
      content_type: 'email',
      risk_score: 72,
      risk_level: 'HIGH',
      detected_indicators: [{ code: 'urgency', label: 'Suspicious urgency', description: 'Pressure to act quickly.', severity: 'medium' }],
      explanation: 'The message contains defensive warning indicators. This is not proof that it is malicious.',
      recommended_actions: ['Verify through a trusted channel.'],
      safe_handling_advice: 'Do not click links until independently verified.',
      created_at: '2026-08-20T10:00:00Z',
    })
    const authValue = {
      user: { id: 1, name: 'Student', email: 'student@example.edu', role: 'student', department: null, year: 2, created_at: '2026-08-19T00:00:00Z', updated_at: '2026-08-19T00:00:00Z' },
      accessToken: 'test-token',
      isAuthenticated: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      authenticatedRequest,
    } as unknown as AuthContextValue

    render(<AuthContext.Provider value={authValue}><MemoryRouter><AnalyzerPage /></MemoryRouter></AuthContext.Provider>)
    await userEvent.type(screen.getByLabelText(/Email content/i), 'Urgent: verify your account now.')
    await userEvent.click(screen.getByRole('button', { name: 'Analyze message' }))

    await waitFor(() => expect(screen.getByRole('heading', { name: 'HIGH' })).toBeInTheDocument())
    expect(screen.getByText('Suspicious urgency')).toBeInTheDocument()
    expect(authenticatedRequest).toHaveBeenCalledWith('/students/analysis/messages', {
      method: 'POST',
      body: JSON.stringify({ content_type: 'email', message: 'Urgent: verify your account now.' }),
    })
  })
})
