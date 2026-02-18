export interface PatientRiskRequest {
  patient_id: string
  age: number
  gender: 'male' | 'female'
  conditions: string[]
  medications: string[]
  recent_encounters: number
  institution_id?: string
}

export interface PatientRiskResponse {
  patient_id: string
  readmission_risk: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  confidence: number
  recommendations: string[]
}

export interface Institution {
  id: string
  name: string
  location: string
  patient_count: number
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  version: string
  services: Record<string, string>
}
