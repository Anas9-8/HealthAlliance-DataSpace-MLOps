import { useEffect, useState } from 'react'
import { ExternalLink, RefreshCw, Brain, Database, Activity, Server, GitBranch, Layers } from 'lucide-react'
import { getServices, getModelInfo } from '../api/client'
import type { ServiceHealth, ModelInfo } from '../types'

// ─── Service Health Card ───────────────────────────────────────────────────────
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
        <span className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-0.5 rounded">:{svc.port}</span>
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

// ─── Arrow marker definition ───────────────────────────────────────────────────
function Defs() {
  return (
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
        markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
      </marker>
      <marker id="arrow-blue" viewBox="0 0 10 10" refX="9" refY="5"
        markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
      </marker>
      <marker id="arrow-green" viewBox="0 0 10 10" refX="9" refY="5"
        markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#22c55e" />
      </marker>
      <marker id="arrow-orange" viewBox="0 0 10 10" refX="9" refY="5"
        markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#f97316" />
      </marker>
    </defs>
  )
}

// ─── Diagram 1: Full Architecture ─────────────────────────────────────────────
function ArchitectureDiagram() {
  // Node dimensions
  const W = 1000, H = 480

  // Node positions [x, y, w, h, label, sublabel, fill, text]
  const nodes = {
    dkfz:       { x: 20,  y: 30,  w: 88, h: 34, label: 'DKFZ',       sub: 'Heidelberg',   fill: '#ede9fe', stroke: '#a78bfa', text: '#5b21b6' },
    ukhd:       { x: 20,  y: 72,  w: 88, h: 34, label: 'UKHD',       sub: 'Heidelberg',   fill: '#ede9fe', stroke: '#a78bfa', text: '#5b21b6' },
    embl:       { x: 20,  y: 114, w: 88, h: 34, label: 'EMBL',       sub: 'Heidelberg',   fill: '#ede9fe', stroke: '#a78bfa', text: '#5b21b6' },
    airflow:    { x: 165, y: 72,  w: 110, h: 44, label: 'Airflow',   sub: ':8085',         fill: '#dcfce7', stroke: '#86efac', text: '#166534' },
    frontend:   { x: 165, y: 185, w: 110, h: 44, label: 'Frontend',  sub: ':5173',         fill: '#dbeafe', stroke: '#93c5fd', text: '#1e40af' },
    fastapi:    { x: 380, y: 148, w: 160, h: 60, label: 'FastAPI',   sub: ':8000  /docs',  fill: '#1e3a5f', stroke: '#1e3a5f', text: '#ffffff' },
    metrics:    { x: 380, y: 270, w: 110, h: 40, label: 'Metrics',   sub: ':8001',         fill: '#fef9c3', stroke: '#fde047', text: '#713f12' },
    mlflow:     { x: 660, y: 72,  w: 110, h: 44, label: 'MLflow',    sub: ':5050',         fill: '#ccfbf1', stroke: '#5eead4', text: '#134e4a' },
    minio:      { x: 660, y: 175, w: 110, h: 44, label: 'MinIO S3',  sub: ':9000/:9001',   fill: '#e0e7ff', stroke: '#a5b4fc', text: '#3730a3' },
    postgres:   { x: 660, y: 278, w: 110, h: 44, label: 'PostgreSQL',sub: ':5432',         fill: '#e0f2fe', stroke: '#7dd3fc', text: '#075985' },
    prometheus: { x: 380, y: 380, w: 120, h: 44, label: 'Prometheus',sub: ':9091',         fill: '#fee2e2', stroke: '#fca5a5', text: '#991b1b' },
    grafana:    { x: 165, y: 380, w: 110, h: 44, label: 'Grafana',   sub: ':3001',         fill: '#ffedd5', stroke: '#fdba74', text: '#9a3412' },
  }

  const n = nodes

  // Edge helper: center of node
  const cx = (nd: typeof n.fastapi) => nd.x + nd.w / 2
  const cy = (nd: typeof n.fastapi) => nd.y + nd.h / 2

  const edge = (
    x1: number, y1: number, x2: number, y2: number,
    label: string, marker = 'url(#arrow)', color = '#94a3b8', dashed = false
  ) => ({ x1, y1, x2, y2, label, marker, color, dashed })

  const edges = [
    edge(n.dkfz.x + n.dkfz.w, cy(n.dkfz), n.airflow.x, cy(n.airflow), 'FHIR R4', 'url(#arrow)', '#a78bfa'),
    edge(n.ukhd.x + n.ukhd.w, cy(n.ukhd), n.airflow.x, cy(n.ukhd), 'FHIR R4', 'url(#arrow)', '#a78bfa'),
    edge(n.embl.x + n.embl.w, cy(n.embl), n.airflow.x + 20, n.airflow.y + n.airflow.h, 'FHIR R4', 'url(#arrow)', '#a78bfa'),
    edge(n.airflow.x + n.airflow.w, cy(n.airflow), n.fastapi.x, n.fastapi.y + 20, 'trigger pipeline', 'url(#arrow-green)', '#22c55e'),
    edge(cx(n.airflow), n.airflow.y + n.airflow.h, cx(n.airflow), n.minio.y + n.minio.h / 2 - 10, 'store data', 'url(#arrow)', '#6366f1', true),
    edge(n.frontend.x + n.frontend.w, cy(n.frontend), n.fastapi.x, n.fastapi.y + 40, 'REST API calls', 'url(#arrow-blue)', '#3b82f6'),
    edge(n.fastapi.x + n.fastapi.w, n.fastapi.y + 20, n.mlflow.x, cy(n.mlflow), 'log experiments', 'url(#arrow)', '#0d9488'),
    edge(n.fastapi.x + n.fastapi.w, n.fastapi.y + 40, n.minio.x, cy(n.minio), 'load model artifact', 'url(#arrow)', '#6366f1', true),
    edge(n.fastapi.x + n.fastapi.w, n.fastapi.y + 55, n.postgres.x, cy(n.postgres), 'SQL queries', 'url(#arrow-blue)', '#0ea5e9'),
    edge(cx(n.fastapi), n.fastapi.y + n.fastapi.h, cx(n.metrics), n.metrics.y, 'expose /metrics', 'url(#arrow-orange)', '#f97316'),
    edge(cx(n.mlflow), n.mlflow.y + n.mlflow.h, cx(n.minio), n.minio.y, 'store artifacts', 'url(#arrow)', '#6366f1'),
    edge(cx(n.prometheus), n.prometheus.y, cx(n.metrics), n.metrics.y + n.metrics.h, 'scrape :8001', 'url(#arrow)', '#ef4444'),
    edge(n.grafana.x + n.grafana.w, cy(n.grafana), n.prometheus.x, cy(n.prometheus), 'PromQL queries', 'url(#arrow-orange)', '#f97316'),
  ]

  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <h3 className="font-semibold text-gray-800 mb-1 flex items-center gap-2">
        <Layers size={16} className="text-blue-600" /> Full Architecture — Service Communication
      </h3>
      <p className="text-xs text-gray-400 mb-4">
        All services and how they communicate. Arrows show data direction and protocol.
      </p>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="block">
          <Defs />

          {/* Layer labels */}
          {[
            { x: 20,  y: 10, label: '① Institutions', color: '#7c3aed' },
            { x: 165, y: 10, label: '② Orchestration', color: '#166534' },
            { x: 380, y: 10, label: '③ Core API', color: '#1e3a5f' },
            { x: 660, y: 10, label: '④ Storage & Tracking', color: '#075985' },
          ].map((l) => (
            <text key={l.label} x={l.x} y={l.y} fontSize={10} fill={l.color} fontWeight="600">{l.label}</text>
          ))}

          {/* Observability label */}
          <text x={165} y={370} fontSize={10} fill="#9a3412" fontWeight="600">⑤ Observability</text>

          {/* Edges */}
          {edges.map((e, i) => {
            const midX = (e.x1 + e.x2) / 2
            const midY = (e.y1 + e.y2) / 2
            return (
              <g key={i}>
                <line
                  x1={e.x1} y1={e.y1} x2={e.x2} y2={e.y2}
                  stroke={e.color} strokeWidth={1.5}
                  strokeDasharray={e.dashed ? '5,4' : undefined}
                  markerEnd={e.marker}
                  opacity={0.8}
                />
                <rect x={midX - 38} y={midY - 8} width={76} height={14} fill="white" opacity={0.85} rx={3} />
                <text x={midX} y={midY + 3} fontSize={8} fill={e.color} textAnchor="middle" fontWeight="500">
                  {e.label}
                </text>
              </g>
            )
          })}

          {/* Nodes */}
          {Object.entries(nodes).map(([key, nd]) => (
            <g key={key}>
              <rect x={nd.x} y={nd.y} width={nd.w} height={nd.h}
                fill={nd.fill} stroke={nd.stroke} strokeWidth={1.5} rx={8} />
              <text x={nd.x + nd.w / 2} y={nd.y + nd.h / 2 - 5}
                fontSize={key === 'fastapi' ? 13 : 11}
                fontWeight="700" fill={nd.text} textAnchor="middle">
                {nd.label}
              </text>
              <text x={nd.x + nd.w / 2} y={nd.y + nd.h / 2 + 9}
                fontSize={8.5} fill={nd.text} textAnchor="middle" opacity={0.75}>
                {nd.sub}
              </text>
            </g>
          ))}

          {/* Legend */}
          <g transform={`translate(795, 360)`}>
            <rect x={0} y={0} width={195} height={110} fill="#f8fafc" stroke="#e2e8f0" rx={6} />
            <text x={10} y={16} fontSize={9} fontWeight="700" fill="#374151">Legend</text>
            {[
              { color: '#a78bfa', label: 'FHIR R4 data ingestion', dashed: false },
              { color: '#22c55e', label: 'Pipeline trigger (Airflow)', dashed: false },
              { color: '#3b82f6', label: 'REST API (Frontend ↔ API)', dashed: false },
              { color: '#f97316', label: 'Metrics scraping (Prometheus)', dashed: false },
              { color: '#6366f1', label: 'Artifact / model storage', dashed: true },
              { color: '#0ea5e9', label: 'SQL database queries', dashed: false },
            ].map((item, i) => (
              <g key={i} transform={`translate(10, ${28 + i * 14})`}>
                <line x1={0} y1={5} x2={20} y2={5}
                  stroke={item.color} strokeWidth={1.5}
                  strokeDasharray={item.dashed ? '4,3' : undefined} />
                <text x={26} y={9} fontSize={8.5} fill="#374151">{item.label}</text>
              </g>
            ))}
          </g>
        </svg>
      </div>
    </div>
  )
}

// ─── Diagram 2: Data Pipeline Flow ────────────────────────────────────────────
function DataPipelineDiagram() {
  const steps = [
    { icon: '🏥', label: 'FHIR R4\nIngestion',   sub: 'DKFZ · UKHD · EMBL', color: '#ede9fe', border: '#a78bfa', text: '#5b21b6' },
    { icon: '🔄', label: 'Airflow DAG',            sub: 'daily schedule',      color: '#dcfce7', border: '#86efac', text: '#166534' },
    { icon: '📦', label: 'DVC + MinIO',            sub: 'versioned storage',   color: '#e0e7ff', border: '#a5b4fc', text: '#3730a3' },
    { icon: '⚙️', label: 'Preprocessing',          sub: 'feature engineering', color: '#fef9c3', border: '#fde047', text: '#713f12' },
    { icon: '🌲', label: 'RandomForest\nTraining', sub: '100 trees, balanced', color: '#dcfce7', border: '#86efac', text: '#166534' },
    { icon: '📊', label: 'MLflow\nTracking',       sub: 'ROC-AUC, params',     color: '#ccfbf1', border: '#5eead4', text: '#134e4a' },
    { icon: '🚀', label: 'FastAPI\nServing',        sub: 'REST + auth',         color: '#1e3a5f', border: '#1e3a5f', text: '#ffffff' },
    { icon: '📈', label: 'Prometheus\nMetrics',    sub: ':8001 scrape',        color: '#fee2e2', border: '#fca5a5', text: '#991b1b' },
    { icon: '📉', label: 'Grafana\nDashboards',    sub: 'live charts',         color: '#ffedd5', border: '#fdba74', text: '#9a3412' },
  ]

  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <h3 className="font-semibold text-gray-800 mb-1 flex items-center gap-2">
        <GitBranch size={16} className="text-green-600" /> Data Pipeline — End-to-End MLOps Flow
      </h3>
      <p className="text-xs text-gray-400 mb-4">
        From raw FHIR patient data at the institution all the way to live Grafana dashboards.
      </p>
      <div className="overflow-x-auto">
        <div className="flex items-center gap-0 min-w-max">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center">
              <div
                className="rounded-xl border-2 p-3 w-28 text-center shrink-0 shadow-sm"
                style={{ background: s.color, borderColor: s.border }}
              >
                <div className="text-2xl mb-1">{s.icon}</div>
                <div className="text-xs font-bold leading-tight whitespace-pre-line" style={{ color: s.text }}>
                  {s.label}
                </div>
                <div className="text-xs mt-1 opacity-70 leading-tight" style={{ color: s.text }}>
                  {s.sub}
                </div>
              </div>
              {i < steps.length - 1 && (
                <div className="flex flex-col items-center w-8 shrink-0">
                  <svg width="32" height="20" viewBox="0 0 32 20">
                    <line x1="2" y1="10" x2="26" y2="10" stroke="#94a3b8" strokeWidth="1.5"
                      markerEnd="url(#arrow)" />
                    <defs>
                      <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5"
                        markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
                      </marker>
                    </defs>
                    <line x1="2" y1="10" x2="26" y2="10" stroke="#94a3b8" strokeWidth="1.5"
                      markerEnd="url(#arr)" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step descriptions */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        {[
          { title: 'Ingestion (steps 1–3)', color: 'bg-purple-50 border-purple-100', items: [
            'Three institutions send FHIR R4 JSON patient records',
            'Airflow DAG schedules daily ingestion runs',
            'Raw data is versioned with DVC and stored in MinIO (S3-compatible)',
          ]},
          { title: 'Training (steps 4–6)', color: 'bg-green-50 border-green-100', items: [
            'Features extracted: age, conditions, medications, encounters, gender',
            'RandomForest trains on 101,763 real patients — ROC-AUC = 0.63',
            'Every run logged to MLflow: params, metrics, model artifact',
          ]},
          { title: 'Serving & Monitoring (steps 7–9)', color: 'bg-orange-50 border-orange-100', items: [
            'FastAPI loads model and serves predictions via REST + JWT auth',
            'Prometheus scrapes /metrics on :8001 every 15 seconds',
            'Grafana visualises API throughput, latency, and model confidence',
          ]},
        ].map((block) => (
          <div key={block.title} className={`rounded-lg border p-3 ${block.color}`}>
            <p className="text-xs font-semibold text-gray-700 mb-2">{block.title}</p>
            <ul className="space-y-1">
              {block.items.map((item, i) => (
                <li key={i} className="text-xs text-gray-600 flex gap-1.5">
                  <span className="shrink-0 mt-0.5">•</span>{item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Diagram 3: Service Communication Map ─────────────────────────────────────
function ServiceCommDiagram() {
  const rows = [
    { from: 'Frontend :5173',   to: 'FastAPI :8000',       proto: 'HTTP REST + JWT Bearer',  dir: '→',  why: 'Login, predict, health, retrain, users' },
    { from: 'FastAPI :8000',    to: 'PostgreSQL :5432',     proto: 'SQL / SQLAlchemy',         dir: '↔',  why: 'Store patient metadata, session data' },
    { from: 'FastAPI :8000',    to: 'MLflow :5050',         proto: 'HTTP REST',                dir: '→',  why: 'Log training params, metrics, model URIs' },
    { from: 'FastAPI :8000',    to: 'Metrics :8001',        proto: 'Prometheus client (push)',  dir: '→',  why: 'Increment counters, observe histograms' },
    { from: 'Airflow :8085',    to: 'FastAPI :8000',        proto: 'HTTP REST / PythonOperator',dir: '→', why: 'Trigger training pipeline DAG' },
    { from: 'Airflow :8085',    to: 'MinIO :9000',          proto: 'S3 API (boto3)',            dir: '↔',  why: 'Read/write FHIR data files (DVC remote)' },
    { from: 'Airflow :8085',    to: 'MLflow :5050',         proto: 'HTTP REST',                dir: '→',  why: 'Create experiment runs from training DAG' },
    { from: 'MLflow :5050',     to: 'MinIO :9000',          proto: 'S3 API',                   dir: '→',  why: 'Store model pkl artifacts and run artifacts' },
    { from: 'Prometheus :9091', to: 'Metrics :8001',        proto: 'HTTP GET /metrics',        dir: '→',  why: 'Scrape Prometheus exposition format every 15s' },
    { from: 'Grafana :3001',    to: 'Prometheus :9091',     proto: 'PromQL over HTTP',         dir: '→',  why: 'Query time-series for dashboard panels' },
    { from: 'Institutions',     to: 'Airflow :8085',        proto: 'FHIR R4 JSON / HTTPS',    dir: '→',  why: 'DKFZ, UKHD, EMBL push patient records' },
  ]

  const dirColor = (d: string) => d === '↔' ? 'text-blue-600' : 'text-gray-600'

  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <h3 className="font-semibold text-gray-800 mb-1 flex items-center gap-2">
        <Activity size={16} className="text-red-500" /> Service Communication Map
      </h3>
      <p className="text-xs text-gray-400 mb-4">
        Every inter-service connection, its protocol, and what data travels across it.
        <span className="ml-2 text-blue-600 font-medium">↔ bidirectional</span>
        <span className="ml-2 text-gray-500 font-medium">→ one-way</span>
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500">From</th>
              <th className="text-center py-2 px-2 text-xs font-semibold text-gray-500">Dir</th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500">To</th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500">Protocol</th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500">Purpose</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className={`border-b last:border-0 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                <td className="py-2 px-3 font-mono text-xs text-blue-700 whitespace-nowrap">{row.from}</td>
                <td className={`py-2 px-2 text-center font-bold text-base ${dirColor(row.dir)}`}>{row.dir}</td>
                <td className="py-2 px-3 font-mono text-xs text-indigo-700 whitespace-nowrap">{row.to}</td>
                <td className="py-2 px-3 text-xs text-gray-500 whitespace-nowrap">{row.proto}</td>
                <td className="py-2 px-3 text-xs text-gray-700">{row.why}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
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
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<Server size={20} className="text-blue-600" />}   label="Services Online"   value={`${healthy} / ${services.length}`} color="blue" />
        <StatCard icon={<Brain size={20} className="text-green-600" />}   label="Model ROC-AUC"     value={modelInfo?.roc_auc ? modelInfo.roc_auc.toFixed(4) : '—'} color="green" />
        <StatCard icon={<Database size={20} className="text-purple-600" />} label="Training Samples" value="101,763" color="purple" />
        <StatCard icon={<Activity size={20} className="text-orange-600" />} label="Institutions"    value="3" color="orange" />
      </div>

      {/* Service health grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-gray-800">Service Health</h2>
          <button onClick={load} className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
        {checkedAt && (
          <p className="text-xs text-gray-400 mb-3">
            Last checked: {new Date(checkedAt).toLocaleTimeString()}
          </p>
        )}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {services.map((svc) => <ServiceCard key={svc.name} svc={svc} />)}
        </div>
      </div>

      {/* Diagram 1 */}
      <ArchitectureDiagram />

      {/* Diagram 2 */}
      <DataPipelineDiagram />

      {/* Diagram 3 */}
      <ServiceCommDiagram />

      {/* Active model info */}
      {modelInfo && (
        <div className="bg-white rounded-xl border shadow-sm p-5">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Brain size={16} className="text-green-600" /> Active Model
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <InfoItem label="Type"        value={modelInfo.model_type} />
            <InfoItem label="Estimators"  value={String(modelInfo.n_estimators)} />
            <InfoItem label="Features"    value={String(modelInfo.features.length)} />
            <InfoItem label="Saved"       value={modelInfo.model_exists ? '✓ On disk' : '✗ Missing'} />
          </div>
          <div className="mt-3">
            <p className="text-xs text-gray-500 mb-1.5">Feature columns used in training</p>
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
