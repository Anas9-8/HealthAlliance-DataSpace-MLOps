import { useState } from 'react'
import PredictionForm from '../components/PredictionForm'
import RiskResult from '../components/RiskResult'
import { predict } from '../api/client'
import type { PatientRiskRequest, PatientRiskResponse } from '../types'

export default function PredictPage() {
  const [result, setResult] = useState<PatientRiskResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (req: PatientRiskRequest) => {
    setLoading(true)
    try {
      const res = await predict(req)
      setResult(res)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Readmission Risk Prediction</h2>
        <p className="text-gray-500 text-sm mt-1">
          Enter patient data to predict 30-day hospital readmission risk using the
          federated ML model trained across DKFZ, UKHD, and EMBL.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PredictionForm onSubmit={handleSubmit} loading={loading} />
        {result && <RiskResult result={result} />}
        {!result && !loading && (
          <div className="hidden lg:flex items-center justify-center bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 min-h-[300px]">
            <p className="text-gray-400 text-sm text-center px-8">
              Fill in patient data and click <strong>Calculate</strong> to see the risk assessment.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
