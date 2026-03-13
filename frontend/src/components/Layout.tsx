import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
        <footer className="px-6 py-2 text-xs text-gray-400 bg-white border-t text-center">
          HealthAlliance DataSpace · GDPR/HIPAA Compliant · DKFZ · UKHD · EMBL
        </footer>
      </div>
    </div>
  )
}
