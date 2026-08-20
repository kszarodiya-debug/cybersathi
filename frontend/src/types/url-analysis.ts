export type URLRiskLevel = 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface URLDetectedIndicator {
  code: string
  label: string
  description: string
  severity: 'low' | 'medium' | 'high'
}

export interface URLAnalysisResult {
  id: number
  url: string
  risk_score: number
  risk_level: URLRiskLevel
  detected_indicators: URLDetectedIndicator[]
  explanation: string
  recommended_action: string
  created_at: string
}
