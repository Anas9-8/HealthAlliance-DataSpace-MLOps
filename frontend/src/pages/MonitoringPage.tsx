import { ExternalLink, BarChart2, Activity, Database, Layers, Wind } from 'lucide-react'

interface ToolCard {
  name: string
  description: string
  url: string
  port: number
  color: string
  icon: JSX.Element
  queries?: string[]
}

const TOOLS: ToolCard[] = [
  {
    name: 'Grafana',
    description: 'Interactive dashboards for API performance and ML metrics. Import the dashboard from monitoring/grafana-dashboard.json.',
    url: 'http://localhost:3001',
    port: 3001,
    color: 'border-orange-200 bg-orange-50',
    icon: <BarChart2 size={20} className="text-orange-600" />,
  },
  {
    name: 'Prometheus',
    description: 'Raw metrics collection and querying. Scrapes the API metrics endpoint every 15 seconds.',
    url: 'http://localhost:9091',
    port: 9091,
    color: 'border-red-200 bg-red-50',
    icon: <Activity size={20} className="text-red-600" />,
    queries: [
      'predictions_total',
      'http_requests_total',
      'http_request_duration_seconds',
      'model_confidence_score',
      'active_connections',
    ],
  },
  {
    name: 'MLflow',
    description: 'Experiment tracking. Shows training run history, parameters, ROC-AUC scores, and feature importance.',
    url: 'http://localhost:5050',
    port: 5050,
    color: 'border-teal-200 bg-teal-50',
    icon: <Layers size={20} className="text-teal-600" />,
  },
  {
    name: 'MinIO Console',
    description: 'S3-compatible object storage. Stores DVC-tracked data files and MLflow model artifacts.',
    url: 'http://localhost:9001',
    port: 9001,
    color: 'border-indigo-200 bg-indigo-50',
    icon: <Database size={20} className="text-indigo-600" />,
  },
  {
    name: 'Apache Airflow',
    description: 'Pipeline scheduler. Runs two DAGs: daily FHIR data ingestion from all 3 institutions, and weekly model retraining. Login: admin / admin123.',
    url: 'http://localhost:8085',
    port: 8085,
    color: 'border-green-200 bg-green-50',
    icon: <Wind size={20} className="text-green-600" />,
  },
]

export default function MonitoringPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <p className="text-sm text-gray-500">
        All monitoring tools run locally via Docker. Click "Open" to launch in a new tab.
        Login for Grafana: <code className="bg-gray-100 px-1 rounded">admin / admin_change_in_production</code>
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {TOOLS.map((tool) => (
          <div key={tool.name} className={`rounded-xl border shadow-sm p-5 ${tool.color}`}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                {tool.icon}
                <h3 className="font-semibold text-gray-800">{tool.name}</h3>
              </div>
              <a href={tool.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-blue-600 hover:underline bg-white border border-blue-200 rounded-lg px-3 py-1.5 font-medium">
                Open <ExternalLink size={11} />
              </a>
            </div>
            <p className="text-sm text-gray-600 mb-3">{tool.description}</p>
            <span className="font-mono text-xs bg-white px-2 py-0.5 rounded border text-gray-600">
              localhost:{tool.port}
            </span>
            {tool.queries && (
              <div className="mt-3">
                <p className="text-xs font-medium text-gray-500 mb-1.5">Example queries</p>
                <div className="flex flex-wrap gap-1.5">
                  {tool.queries.map((q) => (
                    <a key={q} href={`${tool.url}/graph?g0.expr=${encodeURIComponent(q)}`}
                      target="_blank" rel="noopener noreferrer"
                      className="text-xs font-mono bg-white border rounded px-2 py-0.5 text-gray-700 hover:bg-gray-50 hover:text-blue-600">
                      {q}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Grafana setup guide */}
      <div className="bg-white rounded-xl border shadow-sm p-5">
        <h3 className="font-semibold text-gray-800 mb-3">How to load the Grafana dashboard</h3>
        <ol className="space-y-2 text-sm text-gray-600 list-decimal list-inside">
          <li>Open <a href="http://localhost:3001" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Grafana (localhost:3001)</a> and login</li>
          <li>Click the <strong>≡ menu</strong> → <strong>Dashboards</strong> → <strong>Import</strong></li>
          <li>Upload the file <code className="bg-gray-100 px-1 rounded">monitoring/grafana-dashboard.json</code></li>
          <li>Click <strong>Import</strong> — done!</li>
        </ol>
      </div>

      {/* Metrics reference */}
      <div className="bg-white rounded-xl border shadow-sm p-5">
        <h3 className="font-semibold text-gray-800 mb-3">Metrics Reference</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="pb-2 font-medium text-gray-500">Metric</th>
                <th className="pb-2 font-medium text-gray-500">Type</th>
                <th className="pb-2 font-medium text-gray-500">Description</th>
              </tr>
            </thead>
            <tbody className="text-gray-700">
              {[
                ['http_requests_total', 'Counter', 'Total API requests by method, endpoint, status'],
                ['http_request_duration_seconds', 'Histogram', 'API response time distribution'],
                ['predictions_total', 'Counter', 'Predictions by risk level (HIGH/MEDIUM/LOW)'],
                ['prediction_duration_seconds', 'Histogram', 'ML inference time distribution'],
                ['model_confidence_score', 'Histogram', 'Distribution of model confidence scores'],
                ['active_connections', 'Gauge', 'Current active HTTP connections'],
              ].map(([name, type, desc]) => (
                <tr key={name} className="border-b last:border-0">
                  <td className="py-2 font-mono text-xs text-blue-700">{name}</td>
                  <td className="py-2 text-xs text-gray-500">{type}</td>
                  <td className="py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
