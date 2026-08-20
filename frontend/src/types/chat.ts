export interface ChatMessage {
  id: number
  message: string
  response: string
  created_at: string
}

export interface ChatHistoryResponse {
  messages: ChatMessage[]
}
