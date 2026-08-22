import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { AuthContext, type AuthContextValue } from '../auth/context'
import { AdminDashboardPage } from './AdminDashboardPage'

const admin = {
  id: 1,
  name: 'Administrator',
  email: 'admin@example.edu',
  role: 'admin' as const,
  department: null,
  year: null,
  created_at: '2026-08-19T00:00:00Z',
  updated_at: '2026-08-19T00:00:00Z',
}

describe('admin dashboard', () => {
  it('renders live aggregate data and excludes credential fields from the user view', async () => {
    const authenticatedRequest = vi.fn()
      .mockResolvedValueOnce({ registered_users: 2, active_users: 1, students: 1, faculty: 0, admins: 1, total_quiz_attempts: 3, total_incident_reports: 2, total_email_analyses: 4, total_url_analyses: 5, awareness_average: 76, generated_at: '2026-08-22T00:00:00Z' })
      .mockResolvedValueOnce({ summary: { total_students: 1, total_faculty: 0, total_users: 2, awareness_average: 76, total_incidents: 2, open_incidents: 1, high_critical_incidents: 1, total_email_analyses: 4, total_url_analyses: 5, quiz_participation: 3, active_users: 1, registered_users: 2, total_quiz_attempts: 3, total_incident_reports: 2 }, incident_trends: [], threat_categories: [], awareness_scores: [], quiz_performance: [], email_risk_levels: [], url_risk_levels: [], generated_at: '2026-08-22T00:00:00Z', awareness_distribution: [], phishing_reports: 1, suspicious_url_analyses: 2, high_risk_url_analyses: 1, high_risk_email_analyses: 1, cyber_incidents: 2 })
      .mockResolvedValueOnce({ registrations: [], quiz_activity: [], lesson_completions: [], email_analyses: [], url_analyses: [], incident_reports: [], generated_at: '2026-08-22T00:00:00Z' })
      .mockResolvedValueOnce({ users: [{ ...admin, lessons_completed: 2, quiz_attempts: 3, average_quiz_score: 84, awareness_score: 76 }], total: 1, page: 1, page_size: 12, total_pages: 1 })
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
    const authValue = { user: admin, accessToken: 'token', isAuthenticated: true, login: vi.fn(), register: vi.fn(), logout: vi.fn(), authenticatedRequest } as unknown as AuthContextValue

    render(<AuthContext.Provider value={authValue}><MemoryRouter><AdminDashboardPage /></MemoryRouter></AuthContext.Provider>)

    await waitFor(() => expect(screen.getByRole('heading', { name: 'CyberSathi Admin Dashboard' })).toBeInTheDocument())
    expect(screen.getAllByText('2').length).toBeGreaterThan(0)
    expect(screen.getByText('Administrator')).toBeInTheDocument()
    expect(screen.queryByText(/password_hash/i)).not.toBeInTheDocument()
    expect(authenticatedRequest).toHaveBeenCalledWith(expect.stringContaining('/admin/stats'))
  })
})
