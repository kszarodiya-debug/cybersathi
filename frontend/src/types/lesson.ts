export interface LessonSummary {
  id: number
  title: string
  description: string
  category: string
  difficulty: string
  completed: boolean
  completed_at: string | null
}

export interface LessonDetail extends LessonSummary {
  introduction: string
  learning_objectives: string[]
  explanation: string
  real_world_example: string
  safety_tips: string[]
  key_takeaways: string[]
}

export interface LessonListResponse {
  lessons: LessonSummary[]
  categories: string[]
  total: number
  completed_count: number
}

export interface LessonCompletionResponse {
  lesson_id: number
  completed: boolean
  completed_at: string
}
