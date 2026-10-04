export interface ChatMessage {
  id: number | null
  message: string
  response: string
  created_at: string
}

export interface ChatHistoryResponse {
  messages: ChatMessage[]
}
