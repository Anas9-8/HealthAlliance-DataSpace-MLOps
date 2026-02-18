import axios from 'axios'
import type {
  HealthStatus,
  Institution,
  PatientRiskRequest,
  PatientRiskResponse,
} from '../types'

const API_KEY = import.meta.env.VITE_API_KEY ?? 'dev-key-dkfz'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

const http = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
  timeout: 10_000,
})

export async function predict(
  request: PatientRiskRequest
): Promise<PatientRiskResponse> {
  const { data } = await http.post<PatientRiskResponse>('/predict', request)
  return data
}

export async function getInstitutions(): Promise<Institution[]> {
  const { data } = await http.get<{ institutions: Institution[] }>('/institutions')
  return data.institutions
}

export async function healthCheck(): Promise<HealthStatus> {
  const { data } = await axios.get<HealthStatus>(`${API_BASE_URL}/health`)
  return data
}
