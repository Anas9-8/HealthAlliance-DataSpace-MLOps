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

export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
}

export interface LoginResponse {
  token: string
  username: string
  role: string
}

export interface ServiceHealth {
  name: string
  description: string
  port: number
  status: 'healthy' | 'unreachable'
  docs: string | null
}

export interface TrainingStatus {
  running: boolean
  started_at: string | null
  completed_at: string | null
  roc_auc: number | null
  error: string | null
  n_samples: number | null
  current_roc_auc: number | null
}

export interface ModelInfo {
  model_type: string
  features: string[]
  n_estimators: number
  roc_auc: number | null
  model_path: string
  model_exists: boolean
  training_status: TrainingStatus
}
