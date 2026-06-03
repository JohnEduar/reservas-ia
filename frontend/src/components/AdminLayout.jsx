import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navClass = ({ isActive }) =>
    `text-sm font-medium transition-colors rounded px-3 py-1.5 ${
      isActive ? 'bg-indigo-700 text-white' : 'text-indigo-200 hover:text-white hover:bg-indigo-700/50'
    }`

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-indigo-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-6">
              <span className="text-lg font-bold text-white">GlampBook Admin</span>
              <div className="hidden sm:flex gap-1">
                <NavLink to="/admin" end className={navClass}>Métricas</NavLink>
                <NavLink to="/admin/accommodations" className={navClass}>Alojamientos</NavLink>
                <NavLink to="/admin/users" className={navClass}>Usuarios</NavLink>
                <NavLink to="/admin/reservations" className={navClass}>Reservas</NavLink>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <NavLink
                to="/dashboard"
                className="text-sm text-indigo-300 hover:text-white transition-colors hidden sm:block"
              >
                Panel huéspedes →
              </NavLink>
              <span className="hidden sm:block text-sm text-indigo-400 truncate max-w-[160px]">
                {user?.full_name || user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-indigo-200 hover:text-white transition-colors"
              >
                Salir
              </button>
            </div>
          </div>
          <div className="sm:hidden flex gap-1 pb-3 overflow-x-auto">
            <NavLink to="/admin" end className={navClass}>Métricas</NavLink>
            <NavLink to="/admin/accommodations" className={navClass}>Alojamientos</NavLink>
            <NavLink to="/admin/users" className={navClass}>Usuarios</NavLink>
            <NavLink to="/admin/reservations" className={navClass}>Reservas</NavLink>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
