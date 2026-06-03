import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navClass = ({ isActive }) =>
    `text-sm font-medium transition-colors ${
      isActive ? 'text-primary-700' : 'text-gray-600 hover:text-gray-900'
    }`

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-8">
              <span className="text-xl font-bold text-primary-700">GlampBook</span>
              <div className="hidden sm:flex gap-6">
                <NavLink to="/dashboard" className={navClass}>Inicio</NavLink>
                <NavLink to="/accommodations" className={navClass}>Alojamientos</NavLink>
                <NavLink to="/reservations" className={navClass}>Mis reservas</NavLink>
                <NavLink to="/profile" className={navClass}>Perfil</NavLink>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="hidden sm:block text-sm text-gray-500 truncate max-w-[160px]">
                {user?.full_name || user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Salir
              </button>
            </div>
          </div>
          {/* Mobile navigation */}
          <div className="sm:hidden flex gap-5 pb-3 overflow-x-auto">
            <NavLink to="/dashboard" className={navClass}>Inicio</NavLink>
            <NavLink to="/accommodations" className={navClass}>Alojamientos</NavLink>
            <NavLink to="/reservations" className={navClass}>Reservas</NavLink>
            <NavLink to="/profile" className={navClass}>Perfil</NavLink>
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
