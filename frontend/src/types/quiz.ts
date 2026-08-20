export interface QuizSummary {
  id: number
  lesson_id: number
  title: string
  description: string
  category: string
  difficulty: string
  question_count: number
  attempt_count: number
  best_score: number | null
  last_score: number | null
}

export interface QuizListResponse {
  quizzes: QuizSummary[]
  categories: string[]
  difficulties: string[]
  total: number
}

export interface QuizQuestion {
  id: number
  question: string
  options: string[]
}

export interface QuizDetail extends QuizSummary {
  questions: QuizQuestion[]
}

export interface QuizAttemptStart {
  attempt_id: number
  quiz_id: number
  title: string
  category: string
  difficulty: string
  questions: QuizQuestion[]
  started_at: string
}

export interface AnswerResult {
  question_id: number
  selected_answer: string
  correct_answer: string
  is_correct: boolean
  explanation: string
}

export interface AwarenessScore {
  overall_score: number
  phishing_score: number
  password_score: number
  privacy_score: number
  browsing_score: number
  mobile_score: number
}

export interface QuizResult {
  attempt_id: number
  quiz_id: number
  score: number
  correct_answers: number
  total_questions: number
  completed_at: string
  results: AnswerResult[]
  awareness_score: AwarenessScore
}

export interface QuizAttemptHistory {
  attempt_id: number
  quiz_id: number
  quiz_title: string
  category: string
  difficulty: string
  score: number
  total_questions: number
  completed_at: string
}

export interface QuizAttemptHistoryResponse {
  attempts: QuizAttemptHistory[]
  total: number
}
