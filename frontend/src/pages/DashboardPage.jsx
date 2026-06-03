import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { reservationsApi } from '../api/reservations'
import ReservationCard from '../components/ReservationCard'
import Spinner from '../components/Spinner'

export default function DashboardPage() {
  const { user } = useAuth()

  const { data: reservations, isLoading } = useQuery({
    queryKey: ['reservations', 'me'],
    queryFn: () => reservationsApi.list({ limit: 200 }),
  })

  const now = new Date()
  const active = (reservations ?? []).filter((r) => r.status === 'confirmed')
  const upcoming = active.filter((r) => new Date(r.check_in) > now)
  const ongoing = active.filter(
    (r) => new Date(r.check_in) <= now && new Date(r.check_out) > now,
  )

  const stats = [
    { label: 'Activas', value: active.length, color: 'text-green-600' },
    { label: 'Próximas', value: upcoming.length, color: 'text-blue-600' },
    { label: 'En curso', value: ongoing.length, color: 'text-yellow-600' },
    { label: 'Total', value: reservations?.length ?? 0, color: 'text-gray-600' },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Hola, {user?.full_name?.split(' ')[0] || 'viajero'}
        </h1>
        <p className="text-gray-500 mt-1">Resumen de tus reservas en GlampBook</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div
            key={s.label}
            className="bg-white rounded-xl border border-gray-200 p-5 text-center"
          >
            <p className={`text-3xl font-bold ${s.color}`}>{isLoading ? '–' : s.value}</p>
            <p className="text-sm text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Reservas activas</h2>
        <Link
          to="/reservations"
          className="text-sm text-primary-600 hover:text-primary-800 font-medium"
        >
          Ver historial completo →
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : active.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500 mb-2">No tienes reservas activas</p>
          <p className="text-sm text-gray-400 mb-4">Explora nuestros alojamientos y haz tu primera reserva</p>
          <Link
            to="/accommodations"
            className="inline-block px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-xl transition-colors"
          >
            Explorar alojamientos
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {active.slice(0, 5).map((r) => (
            <ReservationCard key={r.id} reservation={r} />
          ))}
          {active.length > 5 && (
            <p className="text-center text-sm text-gray-400 pt-2">
              y {active.length - 5} más —{' '}
              <Link to="/reservations" className="text-primary-600 hover:underline">
                ver todas
              </Link>
            </p>
          )}
        </div>
      )}
    </div>
  )
}
