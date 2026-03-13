import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { healthCheck } from '../api/client'

export default function Header() {
  const [healthy, setHealthy] = useState<boolean | null>(null)
  const location = useLocation()

  useEffect(() => {
    healthCheck()
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false))
  }, [])

  const navItem = (to: string, label: string) => (
    <Link
      to={to}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        location.pathname === to
          ? 'bg-primary-700 text-white'
          : 'text-blue-100 hover:bg-primary-700 hover:text-white'
      }`}
    >
      {label}
    </Link>
  )

  return (
    <header className="bg-primary-900 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-400 rounded-full flex items-center justify-center text-white font-bold text-sm">
            HA
          </div>
          <div>
            <h1 className="text-white text-lg font-semibold leading-none">
              HealthAlliance DataSpace
            </h1>
            <p className="text-blue-300 text-xs">DKFZ · UKHD · EMBL</p>
          </div>
        </div>

        <nav className="flex gap-2">
          {navItem('/', 'Predict')}
          {navItem('/institutions', 'Institutions')}
        </nav>

        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
              healthy === null
                ? 'bg-gray-600 text-gray-200'
                : healthy
                ? 'bg-green-700 text-green-100'
                : 'bg-red-700 text-red-100'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                healthy === null ? 'bg-gray-400' : healthy ? 'bg-green-300' : 'bg-red-300'
              }`}
            />
            {healthy === null ? 'Checking…' : healthy ? 'API Online' : 'API Offline'}
          </span>
        </div>
      </div>
    </header>
  )
}
