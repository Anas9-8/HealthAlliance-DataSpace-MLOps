import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Header from './components/Header'
import PredictPage from './pages/PredictPage'
import InstitutionsPage from './pages/InstitutionsPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<PredictPage />} />
            <Route path="/institutions" element={<InstitutionsPage />} />
          </Routes>
        </main>
        <footer className="mt-12 pb-6 text-center text-xs text-gray-400">
          HealthAlliance DataSpace · GDPR/HIPAA Compliant · DKFZ · UKHD · EMBL
        </footer>
      </div>
    </BrowserRouter>
  )
}
