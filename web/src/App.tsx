import { Routes, Route } from 'react-router-dom'
import AuthGuard from '@/components/AuthGuard'
import Login from '@/pages/Login'
import Register from '@/pages/Register'

function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white mb-2">FairShare</h1>
        <p className="text-gray-500">Split expenses fairly with friends</p>
        <p className="text-gray-600 text-sm mt-4">Dashboard coming in Story 7</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/*"
        element={
          <AuthGuard>
            <Dashboard />
          </AuthGuard>
        }
      />
    </Routes>
  )
}
