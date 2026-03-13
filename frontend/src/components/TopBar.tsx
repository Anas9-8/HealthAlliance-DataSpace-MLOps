import { useEffect, useState } from 'react'
import { LogOut, User, Wifi, WifiOff } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { healthCheck } from '../api/client'

const TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/predict': 'Predict Readmission Risk',
  '/institutions': 'Partner Institutions',
  '/monitoring': 'Monitoring & Metrics',
  '/admin': 'Admin Panel',
}

export default function TopBar() {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    healthCheck().then(() => setOnline(true)).catch(() => setOnline(false))
    const id = setInterval(() => {
      healthCheck().then(() => setOnline(true)).catch(() => setOnline(false))
    }, 30_000)
    return () => clearInterval(id)
  }, [])

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <header className="bg-white border-b px-6 py-3 flex items-center justify-between shrink-0 shadow-sm">
      <h1 className="text-lg font-semibold text-gray-800">
        {TITLES[location.pathname] ?? 'HealthAlliance'}
      </h1>

      <div className="flex items-center gap-4">
        {/* API Status */}
        <span className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${
          online === null ? 'bg-gray-100 text-gray-500'
          : online ? 'bg-green-100 text-green-700'
          : 'bg-red-100 text-red-700'
        }`}>
          {online ? <Wifi size={12} /> : <WifiOff size={12} />}
          {online === null ? 'Checking…' : online ? 'API Online' : 'API Offline'}
        </span>

        {/* User badge */}
        <div className="flex items-center gap-2">
          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold ${
            isAdmin ? 'bg-amber-500' : 'bg-blue-500'
          }`}>
            <User size={14} />
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-gray-700">{user?.username}</p>
            <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-600 transition-colors"
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  )
}
