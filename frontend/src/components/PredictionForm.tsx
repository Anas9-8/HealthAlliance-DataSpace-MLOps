import { useState, useEffect } from 'react'
import type { PatientRiskRequest } from '../types'

interface Props {
  onSubmit: (req: PatientRiskRequest) => Promise<void>
  loading: boolean
  initialValues?: PatientRiskRequest | null
}

const INSTITUTIONS = [
  { id: 'dkfz', name: 'DKFZ — German Cancer Research Center' },
  { id: 'ukhd', name: 'UKHD — University Hospital Heidelberg' },
  { id: 'embl', name: 'EMBL — European Molecular Biology Laboratory' },
]

export default function PredictionForm({ onSubmit, loading, initialValues }: Props) {
  const [patientId, setPatientId] = useState('')
  const [age, setAge] = useState('')
  const [gender, setGender] = useState<'male' | 'female'>('male')
  const [institutionId, setInstitutionId] = useState('dkfz')
  const [conditionsRaw, setConditionsRaw] = useState('')
  const [medicationsRaw, setMedicationsRaw] = useState('')
  const [encounters, setEncounters] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!initialValues) return
    setPatientId(initialValues.patient_id)
    setAge(String(initialValues.age))
    setGender(initialValues.gender)
    setInstitutionId(initialValues.institution_id ?? 'dkfz')
    setConditionsRaw(initialValues.conditions.join(', '))
    setMedicationsRaw(initialValues.medications.join(', '))
    setEncounters(String(initialValues.recent_encounters))
  }, [initialValues])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!patientId.trim()) { setError('Patient ID is required'); return }
    if (!age || Number(age) < 0) { setError('Age must be a non-negative number'); return }
    if (!encounters || Number(encounters) < 0) { setError('Recent encounters must be a non-negative number'); return }

    const req: PatientRiskRequest = {
      patient_id: patientId.trim(),
      age: Number(age),
      gender,
      institution_id: institutionId,
      conditions: conditionsRaw.split(',').map((s) => s.trim()).filter(Boolean),
      medications: medicationsRaw.split(',').map((s) => s.trim()).filter(Boolean),
      recent_encounters: Number(encounters),
    }
    try { await onSubmit(req) }
    catch { setError('Prediction request failed. Check that the API is running.') }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
      <h2 className="text-base font-semibold text-gray-800">Patient Risk Assessment</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-md text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Patient ID</label>
          <input type="text" value={patientId} onChange={(e) => setPatientId(e.target.value)}
            placeholder="e.g. DKFZ-001"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Institution</label>
          <select value={institutionId} onChange={(e) => setInstitutionId(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            {INSTITUTIONS.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Age</label>
          <input type="number" min={0} max={120} value={age} onChange={(e) => setAge(e.target.value)}
            placeholder="e.g. 72"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Gender</label>
          <select value={gender} onChange={(e) => setGender(e.target.value as 'male' | 'female')}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className="block text-xs font-medium text-gray-700 mb-1">Recent Encounters (last 90 days)</label>
          <input type="number" min={0} value={encounters} onChange={(e) => setEncounters(e.target.value)}
            placeholder="e.g. 4"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Active Conditions <span className="text-gray-400 font-normal">(comma-separated)</span>
        </label>
        <input type="text" value={conditionsRaw} onChange={(e) => setConditionsRaw(e.target.value)}
          placeholder="e.g. diabetes, hypertension, CHF"
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Active Medications <span className="text-gray-400 font-normal">(comma-separated)</span>
        </label>
        <input type="text" value={medicationsRaw} onChange={(e) => setMedicationsRaw(e.target.value)}
          placeholder="e.g. metformin, lisinopril, warfarin"
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <button type="submit" disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm">
        {loading ? 'Calculating…' : 'Calculate Readmission Risk'}
      </button>
    </form>
  )
}
