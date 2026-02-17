import { useEffect, useState } from 'react'
import InstitutionCard from '../components/InstitutionCard'
import { getInstitutions } from '../api/client'
import type { Institution } from '../types'

export default function InstitutionsPage() {
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getInstitutions()
      .then(setInstitutions)
      .catch(() => setError('Failed to load institutions. Is the API running?'))
      .finally(() => setLoading(false))
  }, [])

  const total = institutions.reduce((s, i) => s + i.patient_count, 0)

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Partner Institutions</h2>
        <p className="text-gray-500 text-sm mt-1">
          Federated network of German research and clinical institutions.
        </p>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            {institutions.map((inst) => (
              <InstitutionCard key={inst.id} institution={inst} />
            ))}
          </div>
          <p className="text-sm text-gray-500 text-right">
            Total patients across network:{' '}
            <span className="font-semibold text-gray-700">{total.toLocaleString()}</span>
          </p>
        </>
      )}
    </div>
  )
}
