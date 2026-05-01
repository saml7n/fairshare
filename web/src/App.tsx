import { Routes, Route } from 'react-router-dom'
import AuthGuard from '@/components/AuthGuard'
import AppShell from '@/components/AppShell'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Dashboard from '@/pages/Dashboard'
import Groups from '@/pages/Groups'
import CreateGroup from '@/pages/CreateGroup'
import GroupDetail from '@/pages/GroupDetail'

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
