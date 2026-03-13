import { useState } from 'react'
import PredictionForm from '../components/PredictionForm'
import RiskResult from '../components/RiskResult'
import { predict } from '../api/client'
import type { PatientRiskRequest, PatientRiskResponse } from '../types'

const DEMO_PATIENTS = [
  { label: 'High-risk elderly', payload: { patient_id: 'DEMO-001', age: 80, gender: 'male' as const, institution_id: 'dkfz', conditions: ['diabetes', 'CHF', 'hypertension'], medications: ['metformin', 'furosemide', 'lisinopril', 'aspirin', 'warfarin', 'digoxin'], recent_encounters: 5 } },
  { label: 'Medium risk', payload: { patient_id: 'DEMO-002', age: 62, gender: 'female' as const, institution_id: 'ukhd', conditions: ['hypertension', 'type2_diabetes'], medications: ['metformin', 'losartan'], recent_encounters: 2 } },
  { label: 'Low-risk young', payload: { patient_id: 'DEMO-003', age: 28, gender: 'male' as const, institution_id: 'embl', conditions: [], medications: [], recent_encounters: 0 } },
]

export default function PredictPage() {
  const [result, setResult] = useState<PatientRiskResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<PatientRiskResponse[]>([])
  const [demoKey, setDemoKey] = useState(0)
  const [demoPayload, setDemoPayload] = useState<PatientRiskRequest | null>(null)

  const handleSubmit = async (req: PatientRiskRequest) => {
    setLoading(true)
    try {
      const res = await predict(req)
      setResult(res)
      setHistory((prev) => [res, ...prev.slice(0, 4)])
    } finally {
      setLoading(false)
    }
  }

  const loadDemo = (payload: PatientRiskRequest) => {
    setDemoPayload(payload)
    setDemoKey((k) => k + 1)
  }

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Demo buttons */}
      <div className="flex flex-wrap gap-2">
        <span className="text-sm text-gray-500 self-center mr-1">Quick demo:</span>
        {DEMO_PATIENTS.map((d) => (
          <button key={d.label} onClick={() => loadDemo(d.payload)}
            className="text-xs bg-white border border-gray-300 hover:border-blue-400 hover:text-blue-600 text-gray-600 rounded-lg px-3 py-1.5 transition-colors">
            {d.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PredictionForm key={demoKey} onSubmit={handleSubmit} loading={loading} initialValues={demoPayload} />
        {result
          ? <RiskResult result={result} />
          : !loading && (
            <div className="hidden lg:flex items-center justify-center bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 min-h-[300px]">
              <p className="text-gray-400 text-sm text-center px-8">
                Fill in patient data and click <strong>Calculate</strong> to see the risk assessment.
              </p>
            </div>
          )
        }
      </div>

      {/* Prediction history */}
      {history.length > 0 && (
        <div className="bg-white rounded-xl border shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Recent Predictions (this session)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left border-b">
                <th className="pb-2 font-medium text-gray-500">Patient ID</th>
                <th className="pb-2 font-medium text-gray-500">Risk Score</th>
                <th className="pb-2 font-medium text-gray-500">Level</th>
                <th className="pb-2 font-medium text-gray-500">Confidence</th>
              </tr></thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-2 font-mono text-gray-700">{h.patient_id}</td>
                    <td className="py-2">{(h.readmission_risk * 100).toFixed(0)}%</td>
                    <td className="py-2">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        h.risk_level === 'HIGH' ? 'bg-red-100 text-red-700'
                        : h.risk_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-green-100 text-green-700'
                      }`}>{h.risk_level}</span>
                    </td>
                    <td className="py-2 text-gray-500">{(h.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
