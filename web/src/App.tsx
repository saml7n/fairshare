import { Routes, Route } from 'react-router-dom'
import AuthGuard from '@/components/AuthGuard'
import AppShell from '@/components/AppShell'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Groups from '@/pages/Groups'
import CreateGroup from '@/pages/CreateGroup'
import GroupDetail from '@/pages/GroupDetail'

function Dashboard() {
  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-white mb-2">Dashboard</h1>
      <p className="text-gray-500 text-sm">Your expense summary across all groups.</p>
      <p className="text-gray-600 text-sm mt-4">Full dashboard coming in Story 7</p>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        element={
          <AuthGuard>
            <AppShell />
          </AuthGuard>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/groups" element={<Groups />} />
        <Route path="/groups/new" element={<CreateGroup />} />
        <Route path="/groups/:id" element={<GroupDetail />} />
      </Route>
    </Routes>
  )
}
