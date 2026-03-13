import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Stethoscope,
  Building2,
  BarChart2,
  ShieldCheck,
  Activity,
} from 'lucide-react'
import { useAuth } from '../auth/AuthContext'

const NAV = [
  { to: '/',             label: 'Dashboard',    icon: LayoutDashboard },
  { to: '/predict',      label: 'Predict Risk', icon: Stethoscope },
  { to: '/institutions', label: 'Institutions', icon: Building2 },
  { to: '/monitoring',   label: 'Monitoring',   icon: BarChart2 },
]

export default function Sidebar() {
  const { isAdmin } = useAuth()

  return (
    <aside className="w-60 bg-[#1e3a5f] flex flex-col shadow-xl shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-blue-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-400 flex items-center justify-center">
            <Activity size={20} className="text-white" />
          </div>
          <div>
            <p className="text-white font-bold text-sm leading-tight">HealthAlliance</p>
            <p className="text-blue-300 text-xs">DataSpace MLOps</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-blue-200 hover:bg-blue-800 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}

        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors mt-2 ${
                isActive
                  ? 'bg-amber-500 text-white'
                  : 'text-amber-300 hover:bg-amber-600 hover:text-white'
              }`
            }
          >
            <ShieldCheck size={18} />
            Admin Panel
          </NavLink>
        )}
      </nav>

      {/* Institutions */}
      <div className="px-5 py-4 border-t border-blue-800">
        <p className="text-blue-400 text-xs mb-2 font-semibold uppercase tracking-wider">Partners</p>
        {['DKFZ', 'UKHD', 'EMBL'].map((inst) => (
          <div key={inst} className="flex items-center gap-2 py-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 shrink-0" />
            <span className="text-blue-300 text-xs">{inst}</span>
          </div>
        ))}
      </div>
    </aside>
  )
}
