import type { PatientRiskResponse } from '../types'

interface Props {
  result: PatientRiskResponse
}

const LEVEL_CONFIG = {
  LOW: {
    color: 'text-health-green',
    bg: 'bg-green-50',
    border: 'border-green-200',
    bar: 'bg-health-green',
    gauge: '#16a34a',
  },
  MEDIUM: {
    color: 'text-health-yellow',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    bar: 'bg-health-yellow',
    gauge: '#ca8a04',
  },
  HIGH: {
    color: 'text-health-red',
    bg: 'bg-red-50',
    border: 'border-red-200',
    bar: 'bg-health-red',
    gauge: '#dc2626',
  },
}

export default function RiskResult({ result }: Props) {
  const cfg = LEVEL_CONFIG[result.risk_level]
  const pct = Math.round(result.readmission_risk * 100)

  return (
    <div
      className={`rounded-xl shadow-md p-6 border animate-fadeIn ${cfg.bg} ${cfg.border}`}
    >
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Risk Assessment Result</h2>

      {/* Gauge */}
      <div className="flex flex-col items-center mb-6">
        <svg viewBox="0 0 120 70" className="w-48">
          {/* Background arc */}
          <path
            d="M10 65 A50 50 0 0 1 110 65"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Filled arc — dash trick on a 157.08-length path */}
          <path
            d="M10 65 A50 50 0 0 1 110 65"
            fill="none"
            stroke={cfg.gauge}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${(result.readmission_risk * 157.08).toFixed(1)} 157.08`}
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
          <text x="60" y="58" textAnchor="middle" fontSize="18" fontWeight="bold" fill={cfg.gauge}>
            {pct}%
          </text>
        </svg>

        <span
          className={`mt-2 text-2xl font-bold ${cfg.color}`}
        >
          {result.risk_level} RISK
        </span>
        <span className="text-sm text-gray-500 mt-1">
          Confidence: {Math.round(result.confidence * 100)}%
        </span>
      </div>

      {/* Risk bar */}
      <div className="mb-5">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Low</span><span>Medium</span><span>High</span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${cfg.bar}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Patient info */}
      <p className="text-sm text-gray-600 mb-4">
        Patient ID: <span className="font-mono font-medium">{result.patient_id}</span>
      </p>

      {/* Recommendations */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Recommendations</h3>
        <ul className="space-y-1.5">
          {result.recommendations.map((rec, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
              <span className={`mt-0.5 text-lg leading-none ${cfg.color}`}>•</span>
              {rec}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
