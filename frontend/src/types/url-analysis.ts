export type URLRiskLevel = 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface URLDetectedIndicator {
  code: string
  label: string
  description: string
  severity: 'low' | 'medium' | 'high'
}

export interface URLInformation {
  protocol: string
  hostname: string
  port: number | null
  path: string
  query_parameter_count: number
}

export interface URLSecurityCheck {
  name: string
  status: 'pass' | 'attention' | 'not_checked'
  details: string
}

export interface URLAnalysisResult {
  id: number | null
  url: string
  url_information: URLInformation
  security_checks: URLSecurityCheck[]
  risk_score: number
  risk_level: URLRiskLevel
  detected_indicators: URLDetectedIndicator[]
  explanation: string
  recommended_action: string
  created_at: string
}
