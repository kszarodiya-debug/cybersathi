export type MessageContentType = 'email' | 'sms' | 'whatsapp' | 'social_media'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface DetectedIndicator {
  code: string
  label: string
  description: string
  severity: 'low' | 'medium' | 'high'
}

export interface MessageAnalysisResult {
  id: number
  content_type: MessageContentType
  risk_score: number
  risk_level: RiskLevel
  detected_indicators: DetectedIndicator[]
  explanation: string
  recommended_actions: string[]
  safe_handling_advice: string
  created_at: string
}
