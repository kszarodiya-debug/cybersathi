export interface AdminUser {
  id: number
  name: string
  email: string
  role: 'student' | 'faculty' | 'admin'
  department: string | null
  year: number | null
  created_at: string
  updated_at: string
  last_login_at?: string | null
  lessons_completed?: number
  quiz_attempts?: number
  average_quiz_score?: number
  awareness_score?: number | null
  phishing_score?: number | null
  password_score?: number | null
  privacy_score?: number | null
  browsing_score?: number | null
}

export interface AdminLesson {
  id: number
  title: string
  category: string
  difficulty: string
  quiz_count: number
  created_at: string
}

export interface AdminQuiz {
  id: number
  lesson_id: number
  title: string
  category: string
  difficulty: string
  question_count: number
  attempt_count: number
}

export interface AdminAnalytics {
  summary: {
    total_students: number
    total_faculty: number
    total_users: number
    awareness_average: number
    total_incidents: number
    open_incidents: number
    high_critical_incidents: number
    total_email_analyses: number
    total_url_analyses: number
    quiz_participation: number
    active_users: number
    registered_users: number
    total_quiz_attempts: number
    total_incident_reports: number
  }
  incident_trends: { label: string; count: number }[]
  threat_categories: { label: string; count: number }[]
  awareness_scores: { label: string; score: number }[]
  quiz_performance: { label: string; attempts: number; average_score: number }[]
  email_risk_levels: { label: string; count: number }[]
  url_risk_levels: { label: string; count: number }[]
  generated_at: string
  awareness_distribution: { label: string; count: number }[]
  phishing_reports: number
  suspicious_url_analyses: number
  high_risk_url_analyses: number
  high_risk_email_analyses: number
  cyber_incidents: number
}

export interface AdminUserPage {
  users: AdminUser[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface AdminStats {
  registered_users: number
  active_users: number
  students: number
  faculty: number
  admins: number
  total_quiz_attempts: number
  total_incident_reports: number
  total_email_analyses: number
  total_url_analyses: number
  awareness_average: number
  generated_at: string
}

export interface AdminActivity {
  registrations: { label: string; count: number }[]
  quiz_activity: { label: string; count: number }[]
  lesson_completions: { label: string; count: number }[]
  email_analyses: { label: string; count: number }[]
  url_analyses: { label: string; count: number }[]
  incident_reports: { label: string; count: number }[]
  generated_at: string
}
