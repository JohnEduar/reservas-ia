import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { usersApi } from '../api/users'
import Spinner from '../components/Spinner'

function LoginForm({ onSuccess }) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const userData = await login(email, password)
      onSuccess(userData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Credenciales incorrectas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {error}
        </div>
      )}
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">Correo electrónico</label>
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="tu@correo.com"
          className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition text-sm"
        />
      </div>
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">Contraseña</label>
        <input
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition text-sm"
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white font-semibold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2 text-sm shadow-sm shadow-primary-200"
      >
        {loading && <Spinner size="sm" />}
        {loading ? 'Ingresando...' : 'Ingresar'}
      </button>
    </form>
  )
}

function RegisterForm({ onRegistered }) {
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (field) => (e) => setForm((p) => ({ ...p, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('Las contraseñas no coinciden')
      return
    }
    if (form.password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      return
    }
    setLoading(true)
    try {
      await usersApi.register({
        full_name: form.full_name,
        email: form.email,
        password: form.password,
      })
      onRegistered(form.email, form.password)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail[0]?.msg : detail || 'Error al crear la cuenta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {error}
        </div>
      )}
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">Nombre completo</label>
        <input
          type="text"
          required
          autoComplete="name"
          value={form.full_name}
          onChange={set('full_name')}
          placeholder="María García"
          className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition text-sm"
        />
      </div>
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">Correo electrónico</label>
        <input
          type="email"
          required
          autoComplete="email"
          value={form.email}
          onChange={set('email')}
          placeholder="tu@correo.com"
          className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition text-sm"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Contraseña</label>
          <input
            type="password"
            required
            autoComplete="new-password"
            value={form.password}
            onChange={set('password')}
            placeholder="••••••••"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition text-sm"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Confirmar</label>
          <input
            type="password"
            required
            autoComplete="new-password"
            value={form.confirm}
            onChange={set('confirm')}
            placeholder="••••••••"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition text-sm"
          />
        </div>
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white font-semibold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2 text-sm shadow-sm shadow-primary-200"
      >
        {loading && <Spinner size="sm" />}
        {loading ? 'Creando cuenta...' : 'Crear cuenta'}
      </button>
    </form>
  )
}

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState('login')

  if (user) return <Navigate to={user.is_superuser ? '/admin' : '/dashboard'} replace />

  const handleLoginSuccess = (userData) => {
    navigate(userData.is_superuser ? '/admin' : '/dashboard')
  }

  const handleRegistered = async (email, password) => {
    try {
      const userData = await login(email, password)
      navigate(userData.is_superuser ? '/admin' : '/dashboard')
    } catch {
      setTab('login')
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-700 via-primary-600 to-emerald-500 flex-col justify-between p-12 relative overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-white/5" />
        <div className="absolute -bottom-32 -right-16 w-[28rem] h-[28rem] rounded-full bg-white/5" />
        <div className="absolute top-1/2 left-1/3 w-64 h-64 rounded-full bg-white/5" />

        <div className="relative">
          <span className="text-white/80 text-sm font-medium tracking-widest uppercase">GlampBook</span>
        </div>

        <div className="relative space-y-6">
          <h1 className="text-5xl font-bold text-white leading-tight">
            Tu próxima<br />escapada<br />te espera.
          </h1>
          <p className="text-primary-100 text-lg leading-relaxed max-w-xs">
            Descubre alojamientos únicos en medio de la naturaleza y reserva en segundos.
          </p>

          <div className="flex gap-6 pt-4">
            <div>
              <p className="text-2xl font-bold text-white">200+</p>
              <p className="text-primary-200 text-sm">Alojamientos</p>
            </div>
            <div className="w-px bg-white/20" />
            <div>
              <p className="text-2xl font-bold text-white">12k+</p>
              <p className="text-primary-200 text-sm">Huéspedes</p>
            </div>
            <div className="w-px bg-white/20" />
            <div>
              <p className="text-2xl font-bold text-white">4.9</p>
              <p className="text-primary-200 text-sm">Valoración</p>
            </div>
          </div>
        </div>

        <p className="relative text-primary-200 text-xs">
          © 2026 GlampBook · Todos los derechos reservados
        </p>
      </div>

      {/* Right panel — form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-8">
            <span className="text-2xl font-bold text-primary-700">GlampBook</span>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900">
              {tab === 'login' ? 'Bienvenido de vuelta' : 'Crea tu cuenta'}
            </h2>
            <p className="text-gray-500 mt-1 text-sm">
              {tab === 'login'
                ? 'Ingresa tus datos para continuar'
                : 'Únete y empieza a explorar'}
            </p>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 p-1 bg-gray-100 rounded-xl mb-8">
            <button
              onClick={() => setTab('login')}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                tab === 'login'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Iniciar sesión
            </button>
            <button
              onClick={() => setTab('register')}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                tab === 'register'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Registrarse
            </button>
          </div>

          {tab === 'login' ? (
            <LoginForm onSuccess={handleLoginSuccess} />
          ) : (
            <RegisterForm onRegistered={handleRegistered} />
          )}

          <p className="mt-6 text-center text-sm text-gray-400">
            {tab === 'login' ? (
              <>
                ¿No tienes cuenta?{' '}
                <button onClick={() => setTab('register')} className="text-primary-600 font-medium hover:underline">
                  Regístrate gratis
                </button>
              </>
            ) : (
              <>
                ¿Ya tienes cuenta?{' '}
                <button onClick={() => setTab('login')} className="text-primary-600 font-medium hover:underline">
                  Inicia sesión
                </button>
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}
