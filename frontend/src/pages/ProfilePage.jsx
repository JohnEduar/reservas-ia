import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { usersApi } from '../api/users'
import Spinner from '../components/Spinner'

export default function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const [form, setForm] = useState({
    full_name: user?.full_name ?? '',
    email: user?.email ?? '',
    password: '',
    passwordConfirm: '',
  })
  const [success, setSuccess] = useState('')
  const [fieldError, setFieldError] = useState('')

  const mutation = useMutation({
    mutationFn: (data) => usersApi.update(data),
    onSuccess: async () => {
      await refreshUser()
      setSuccess('Perfil actualizado correctamente')
      setForm((f) => ({ ...f, password: '', passwordConfirm: '' }))
      setTimeout(() => setSuccess(''), 4000)
    },
    onError: (err) => {
      setFieldError(err.response?.data?.detail || 'Error al actualizar el perfil')
    },
  })

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
    setSuccess('')
    setFieldError('')
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (form.password && form.password !== form.passwordConfirm) {
      setFieldError('Las contraseñas no coinciden')
      return
    }
    const payload = {}
    if (form.full_name !== (user?.full_name ?? '')) payload.full_name = form.full_name || null
    if (form.email !== user?.email) payload.email = form.email
    if (form.password) payload.password = form.password
    if (Object.keys(payload).length === 0) {
      setFieldError('No hay cambios que guardar')
      return
    }
    mutation.mutate(payload)
  }

  const initials = (user?.full_name || user?.email || '?')[0].toUpperCase()

  return (
    <div className="max-w-lg mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Mi perfil</h1>
        <p className="text-gray-500 mt-1">Administra tu información personal</p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-100">
          <div className="h-14 w-14 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 text-xl font-bold shrink-0">
            {initials}
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 truncate">{user?.full_name || '—'}</p>
            <p className="text-sm text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>

        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            {success}
          </div>
        )}
        {fieldError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {fieldError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
              Nombre completo
            </label>
            <input
              id="full_name"
              name="full_name"
              type="text"
              value={form.full_name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
              placeholder="Tu nombre"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={form.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
            />
          </div>

          <div className="border-t border-gray-100 pt-4">
            <p className="text-sm font-medium text-gray-700 mb-3">Cambiar contraseña</p>
            <div className="space-y-3">
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                minLength={form.password ? 8 : undefined}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
                placeholder="Nueva contraseña (mínimo 8 caracteres)"
              />
              <input
                name="passwordConfirm"
                type="password"
                value={form.passwordConfirm}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
                placeholder="Confirmar nueva contraseña"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="w-full py-2.5 px-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {mutation.isPending && <Spinner size="sm" />}
              {mutation.isPending ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </div>
        </form>
      </div>

      <div className="mt-4 bg-white rounded-2xl border border-gray-200 p-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Información de cuenta</h2>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">ID de usuario</dt>
            <dd className="font-medium text-gray-900">#{user?.id}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Estado</dt>
            <dd>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                  user?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}
              >
                {user?.is_active ? 'Activa' : 'Inactiva'}
              </span>
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Miembro desde</dt>
            <dd className="font-medium text-gray-900">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('es-ES', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                  })
                : '—'}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  )
}
