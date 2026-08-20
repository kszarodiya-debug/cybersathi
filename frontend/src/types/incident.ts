export type IncidentType =
  | 'phishing'
  | 'suspicious_link'
  | 'account_compromise'
  | 'cyberbullying'
  | 'malware'
  | 'data_leakage'
  | 'online_scam'
  | 'fake_website'
  | 'other'

export type IncidentStatus = 'OPEN' | 'UNDER_REVIEW' | 'RESOLVED' | 'REJECTED'
export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface IncidentReport {
  id: number
  user_id: number
  incident_type: IncidentType
  description: string
  suspicious_url: string | null
  occurred_at: string
  evidence_metadata: Record<string, string>
  status: IncidentStatus
  severity: IncidentSeverity
  created_at: string
  updated_at: string
}

export interface IncidentReportListResponse {
  reports: IncidentReport[]
  total: number
}

export interface AdminIncidentReport extends IncidentReport {
  reporter_name: string
  reporter_email: string
  reporter_department: string | null
}

export interface AdminIncidentReportListResponse {
  reports: AdminIncidentReport[]
  total: number
}
