import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'

import { useAuth } from './auth/useAuth'
import { Footer } from './components/Footer'
import { Navbar } from './components/Navbar'
import { AuthPages } from './pages/AuthPages'
import { AnalyzerPage } from './pages/AnalyzerPage'
import { ChatPage } from './pages/ChatPage'
import { DashboardPage } from './pages/DashboardPage'
import { AdminIncidentsPage } from './pages/AdminIncidentsPage'
import { AdminDashboardPage } from './pages/AdminDashboardPage'
import { IncidentReportingPage } from './pages/IncidentReportingPage'
import { LandingPage } from './pages/LandingPage'
import { LearningHubPage } from './pages/LearningHubPage'
import { LessonDetailPage } from './pages/LessonDetailPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { QuizPage } from './pages/QuizPage'
import { URLAnalyzerPage } from './pages/URLAnalyzerPage'

function SiteLayout() {
  return <div className="flex min-h-screen flex-col bg-mist text-ink"><Navbar /><main className="flex-1"><Outlet /></main><Footer /></div>
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}

function StudentRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (user?.role !== 'student') return <Navigate to="/" replace />
  return children
}

function AdminRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (user?.role !== 'admin') return <Navigate to="/" replace />
  return children
}

export default function App() {
  return <BrowserRouter basename={import.meta.env.BASE_URL}><Routes><Route element={<SiteLayout />}><Route path="/" element={<LandingPage />} /><Route path="/login" element={<AuthPages mode="login" />} /><Route path="/register" element={<AuthPages mode="register" />} /><Route path="/ask" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} /><Route path="/analyze-email" element={<ProtectedRoute><AnalyzerPage /></ProtectedRoute>} /><Route path="/check-url" element={<ProtectedRoute><URLAnalyzerPage /></ProtectedRoute>} /><Route path="/report-incident" element={<ProtectedRoute><StudentRoute><IncidentReportingPage /></StudentRoute></ProtectedRoute>} /><Route path="/report-incident/:reportId" element={<ProtectedRoute><StudentRoute><IncidentReportingPage /></StudentRoute></ProtectedRoute>} /><Route path="/admin" element={<ProtectedRoute><AdminRoute><AdminDashboardPage /></AdminRoute></ProtectedRoute>} /><Route path="/admin/incidents" element={<ProtectedRoute><AdminRoute><AdminIncidentsPage /></AdminRoute></ProtectedRoute>} /><Route path="/learn" element={<ProtectedRoute><LearningHubPage /></ProtectedRoute>} /><Route path="/learn/:lessonId" element={<ProtectedRoute><LessonDetailPage /></ProtectedRoute>} /><Route path="/quiz" element={<ProtectedRoute><QuizPage /></ProtectedRoute>} /><Route path="/dashboard" element={<ProtectedRoute><StudentRoute><DashboardPage /></StudentRoute></ProtectedRoute>} /><Route path="*" element={<NotFoundPage />} /></Route></Routes></BrowserRouter>
}
