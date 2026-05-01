/** App shell with bottom navigation for mobile-first layout. */

import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { clearToken, getUserInfo } from '@/lib/auth'
import { LayoutDashboard, Users, LogOut } from 'lucide-react'

export default function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const user = getUserInfo()

  const handleLogout = () => {
    clearToken()
    navigate('/login')
  }

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Home' },
    { path: '/groups', icon: Users, label: 'Groups' },
  ]

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Top bar */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <span className="text-white font-bold">FairShare</span>
        <div className="flex items-center gap-3">
          <span className="text-gray-400 text-sm">{user?.name}</span>
          <button onClick={handleLogout} className="text-gray-500 hover:text-white transition" title="Log out">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 pb-16">
        <Outlet />
      </main>

      {/* Bottom nav */}
      <nav className="fixed bottom-0 inset-x-0 bg-gray-900 border-t border-gray-800 flex">
        {navItems.map((item) => {
          const active = location.pathname === item.path ||
            (item.path !== '/' && location.pathname.startsWith(item.path))
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`flex-1 flex flex-col items-center py-2 text-xs transition ${
                active ? 'text-indigo-400' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <item.icon className="w-5 h-5 mb-0.5" />
              {item.label}
            </button>
          )
        })}
      </nav>
    </div>
  )
}
