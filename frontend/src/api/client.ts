import axios from 'axios'
import type {
  HealthStatus,
  Institution,
  LoginResponse,
  ModelInfo,
  PatientRiskRequest,
  PatientRiskResponse,
  ServiceHealth,
  TrainingStatus,
  User,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

const http = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

// Attach auth header dynamically
http.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem('ha_user')
    if (stored) {
      const { token } = JSON.parse(stored)
      if (token) config.headers['Authorization'] = `Bearer ${token}`
    }
  } catch { /* ignore */ }
  return config
})

// ---------- Auth ----------
export async function loginApi(username: string, password: string): Promise<LoginResponse> {
  const { data } = await http.post<LoginResponse>('/auth/login', { username, password })
  return data
}

// ---------- Predict (also send X-API-Key for backward compat) ----------
export async function predict(request: PatientRiskRequest): Promise<PatientRiskResponse> {
  const keyMap: Record<string, string> = {
    dkfz: 'dev-key-dkfz',
    ukhd: 'dev-key-ukhd',
    embl: 'dev-key-embl',
  }
  const apiKey = keyMap[request.institution_id ?? 'dkfz'] ?? 'dev-key-dkfz'
  const { data } = await http.post<PatientRiskResponse>('/predict', request, {
    headers: { 'X-API-Key': apiKey },
  })
  return data
}

// ---------- Institutions ----------
export async function getInstitutions(): Promise<Institution[]> {
  const { data } = await http.get<{ institutions: Institution[] }>('/institutions', {
    headers: { 'X-API-Key': 'dev-key-dkfz' },
  })
  return data.institutions
}

// ---------- Health ----------
export async function healthCheck(): Promise<HealthStatus> {
  const { data } = await axios.get<HealthStatus>(`${API_BASE_URL}/health`)
  return data
}

// ---------- Services ----------
export async function getServices(): Promise<{ services: ServiceHealth[]; checked_at: string }> {
  const { data } = await http.get('/services')
  return data
}

// ---------- Model ----------
export async function getModelInfo(): Promise<ModelInfo> {
  const { data } = await http.get<ModelInfo>('/model/info')
  return data
}

// ---------- Admin: Users ----------
export async function getUsers(): Promise<User[]> {
  const { data } = await http.get<{ users: User[] }>('/admin/users')
  return data.users
}

export async function createUser(username: string, password: string, role: string): Promise<void> {
  await http.post('/admin/users', { username, password, role })
}

export async function deleteUser(id: number): Promise<void> {
  await http.delete(`/admin/users/${id}`)
}

// ---------- Admin: Retrain ----------
export async function triggerRetrain(n_patients: number): Promise<void> {
  await http.post('/admin/retrain', { n_patients })
}

export async function getRetrainStatus(): Promise<TrainingStatus> {
  const { data } = await http.get<TrainingStatus>('/admin/retrain/status')
  return data
}
