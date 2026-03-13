import { useEffect, useState } from 'react'
import { ExternalLink, RefreshCw, Brain, Database, Activity, Server } from 'lucide-react'
import { getServices, getModelInfo } from '../api/client'
import type { ServiceHealth, ModelInfo } from '../types'

function ServiceCard({ svc }: { svc: ServiceHealth }) {
  const ok = svc.status === 'healthy'
  return (
    <div className={`bg-white rounded-xl p-4 border shadow-sm flex flex-col gap-2 ${ok ? 'border-green-100' : 'border-red-100'}`}>
      <div className="flex items-center justify-between">
        <span className="font-semibold text-gray-800 text-sm">{svc.name}</span>
        <span className={`flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${ok ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'}`} />
          {ok ? 'Healthy' : 'Unreachable'}
        </span>
      </div>
      <p className="text-xs text-gray-500">{svc.description}</p>
      <div className="flex items-center justify-between mt-auto pt-1">
        <span className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
          :{svc.port}
        </span>
        {svc.docs && (
          <a href={svc.docs} target="_blank" rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:underline flex items-center gap-1">
            Open <ExternalLink size={10} />
          </a>
        )}
      </div>
    </div>
  )
}

function ArchDiagram() {
  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Activity size={16} className="text-blue-600" /> Information Flow
      </h3>
      <div className="overflow-x-auto">
        <div className="flex items-center gap-2 min-w-max text-sm">
          {/* Hospitals */}
          <div className="flex flex-col gap-1">
            {['DKFZ', 'UKHD', 'EMBL'].map((h) => (
              <div key={h} className="bg-purple-100 text-purple-800 text-xs font-mono px-3 py-1.5 rounded-lg border border-purple-200">
                {h}
              </div>
            ))}
          </div>
          <Arrow label="FHIR R4" />
          {/* API */}
          <Box color="bg-blue-100 border-blue-300 text-blue-800" label="FastAPI" sub=":8000" />
          <Arrow label="features" />
          {/* Model */}
          <Box color="bg-green-100 border-green-300 text-green-800" label="RandomForest" sub="sklearn" />
          <Arrow label="risk score" />
          {/* Response */}
          <Box color="bg-orange-100 border-orange-300 text-orange-800" label="HIGH/MED/LOW" sub="+ recs" />
        </div>

        <div className="flex items-start gap-2 min-w-max text-sm mt-4 ml-20">
          <div className="flex flex-col items-center gap-1 mt-1">
            <div className="w-px h-4 bg-gray-300" />
            <span className="text-gray-400 text-xs">metrics</span>
            <div className="w-px h-4 bg-gray-300" />
          </div>
          <Box color="bg-red-100 border-red-300 text-red-800" label="Prometheus" sub=":9091" />
          <Arrow label="scrape" />
          <Box color="bg-yellow-100 border-yellow-300 text-yellow-800" label="Grafana" sub=":3001" />
          <div className="ml-4 flex flex-col items-center gap-1 mt-1">
            <div className="w-px h-4 bg-gray-300" />
            <span className="text-gray-400 text-xs">logs runs</span>
            <div className="w-px h-4 bg-gray-300" />
          </div>
          <Box color="bg-teal-100 border-teal-300 text-teal-800" label="MLflow" sub=":5050" />
        </div>

        <div className="flex items-start gap-2 min-w-max text-sm mt-4 ml-20">
          <Box color="bg-gray-100 border-gray-300 text-gray-800" label="PostgreSQL" sub=":5432" />
          <Arrow label="artifact store" />
          <Box color="bg-indigo-100 border-indigo-300 text-indigo-800" label="MinIO S3" sub=":9000" />
          <div className="ml-4 flex flex-col items-center gap-1 mt-1">
            <div className="w-px h-4 bg-gray-300" />
            <span className="text-gray-400 text-xs">schedules</span>
            <div className="w-px h-4 bg-gray-300" />
          </div>
          <Box color="bg-pink-100 border-pink-300 text-pink-800" label="Airflow" sub="DAGs" />
        </div>
      </div>
    </div>
  )
}

function Arrow({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center gap-0.5 shrink-0">
      <span className="text-gray-400 text-xs whitespace-nowrap">{label}</span>
      <span className="text-gray-400 text-lg leading-none">→</span>
    </div>
  )
}

function Box({ color, label, sub }: { color: string; label: string; sub: string }) {
  return (
    <div className={`${color} border text-xs font-semibold px-3 py-2 rounded-lg text-center shrink-0`}>
      <div>{label}</div>
      <div className="font-mono font-normal opacity-70">{sub}</div>
    </div>
  )
}

export default function DashboardPage() {
  const [services, setServices] = useState<ServiceHealth[]>([])
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [checkedAt, setCheckedAt] = useState('')

  const load = () => {
    setLoading(true)
    Promise.all([getServices(), getModelInfo()])
      .then(([svcData, mi]) => {
        setServices(svcData.services)
        setCheckedAt(svcData.checked_at)
        setModelInfo(mi)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const healthy = services.filter((s) => s.status === 'healthy').length

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<Server size={20} className="text-blue-600" />} label="Services Online" value={`${healthy} / ${services.length}`} color="blue" />
        <StatCard icon={<Brain size={20} className="text-green-600" />} label="Model ROC-AUC" value={modelInfo?.roc_auc ? modelInfo.roc_auc.toFixed(4) : '—'} color="green" />
        <StatCard icon={<Database size={20} className="text-purple-600" />} label="Training Samples" value="1,000" color="purple" />
        <StatCard icon={<Activity size={20} className="text-orange-600" />} label="Institutions" value="3" color="orange" />
      </div>

      {/* Service health */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-gray-800">Service Health</h2>
          <button onClick={load} className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
        {checkedAt && (
          <p className="text-xs text-gray-400 mb-3">Last checked: {new Date(checkedAt).toLocaleTimeString()}</p>
        )}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {services.map((svc) => <ServiceCard key={svc.name} svc={svc} />)}
        </div>
      </div>

      {/* Architecture */}
      <ArchDiagram />

      {/* Model info */}
      {modelInfo && (
        <div className="bg-white rounded-xl border shadow-sm p-5">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Brain size={16} className="text-green-600" /> Active Model
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <InfoItem label="Type" value={modelInfo.model_type} />
            <InfoItem label="Estimators" value={String(modelInfo.n_estimators)} />
            <InfoItem label="Features" value={String(modelInfo.features.length)} />
            <InfoItem label="File" value={modelInfo.model_exists ? '✓ Saved' : '✗ Missing'} />
          </div>
          <div className="mt-3">
            <p className="text-xs text-gray-500 mb-1">Feature columns</p>
            <div className="flex flex-wrap gap-1.5">
              {modelInfo.features.map((f) => (
                <span key={f} className="bg-gray-100 text-gray-700 text-xs font-mono px-2 py-0.5 rounded">{f}</span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, label, value, color }: { icon: JSX.Element; label: string; value: string; color: string }) {
  const bg = { blue: 'bg-blue-50', green: 'bg-green-50', purple: 'bg-purple-50', orange: 'bg-orange-50' }[color]
  return (
    <div className={`${bg} rounded-xl p-4 border border-transparent shadow-sm`}>
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-xs text-gray-500">{label}</span></div>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
    </div>
  )
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-semibold text-gray-800">{value}</p>
    </div>
  )
}
