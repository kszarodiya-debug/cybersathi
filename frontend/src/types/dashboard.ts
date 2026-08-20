import type { AuthUser } from '../auth/types'

export interface AwarenessScore {
  overall_score: number
  phishing_score: number
  password_score: number
  privacy_score: number
  browsing_score: number
  mobile_score: number
}

export interface QuizScore {
  attempt_id: number
  quiz_id: number
  quiz_title: string
  score: number
  total_questions: number
  completed_at: string
}

export interface LearningProgress {
  completed_lessons: number
  quiz_scores: QuizScore[]
  current_streak: number
}

export interface RecentEmailAnalysis {
  id: number
  risk_score: number
  risk_level: string
  created_at: string
}

export interface RecentURLAnalysis {
  id: number
  url: string
  risk_score: number
  risk_level: string
  created_at: string
}

export interface RecentReport {
  id: number
  incident_type: string
  status: string
  severity: string
  created_at: string
}

export interface RecentActivity {
  email_analyses: RecentEmailAnalysis[]
  url_analyses: RecentURLAnalysis[]
  quizzes: QuizScore[]
  reports: RecentReport[]
}

export interface StudentDashboard {
  user: AuthUser
  awareness_score: AwarenessScore | null
  learning_progress: LearningProgress
  recent_activity: RecentActivity
}
