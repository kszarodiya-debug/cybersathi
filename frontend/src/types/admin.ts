export interface AdminUser {
  id: number
  name: string
  email: string
  role: 'student' | 'faculty' | 'admin'
  department: string | null
  year: number | null
  created_at: string
  updated_at: string
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
  }
  incident_trends: { label: string; count: number }[]
  threat_categories: { label: string; count: number }[]
  awareness_scores: { label: string; score: number }[]
  quiz_performance: { label: string; attempts: number; average_score: number }[]
  email_risk_levels: { label: string; count: number }[]
  url_risk_levels: { label: string; count: number }[]
  generated_at: string
}
