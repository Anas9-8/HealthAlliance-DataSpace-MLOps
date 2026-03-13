import type { Institution } from '../types'

interface Props {
  institution: Institution
}

const COLORS: Record<string, string> = {
  dkfz: 'bg-blue-100 text-blue-800',
  ukhd: 'bg-green-100 text-green-800',
  embl: 'bg-purple-100 text-purple-800',
}

export default function InstitutionCard({ institution }: Props) {
  const badge = COLORS[institution.id] ?? 'bg-gray-100 text-gray-800'

  return (
    <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-base font-semibold text-gray-800">{institution.name}</h3>
        <span className={`text-xs font-mono font-medium px-2 py-0.5 rounded-full uppercase ${badge}`}>
          {institution.id}
        </span>
      </div>
      <p className="text-sm text-gray-500 mb-4">{institution.location}</p>
      <div className="border-t border-gray-100 pt-3">
        <p className="text-sm text-gray-600">
          <span className="font-semibold text-primary-700">
            {institution.patient_count.toLocaleString()}
          </span>{' '}
          patients
        </p>
      </div>
    </div>
  )
}
