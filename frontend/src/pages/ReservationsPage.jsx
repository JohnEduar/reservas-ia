import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { reservationsApi } from '../api/reservations'
import ReservationCard from '../components/ReservationCard'
import Spinner from '../components/Spinner'

const FILTERS = [
  { label: 'Todas', value: 'all' },
  { label: 'Activas', value: 'confirmed' },
  { label: 'Canceladas', value: 'cancelled' },
]

export default function ReservationsPage() {
  const [filter, setFilter] = useState('all')

  const { data: reservations, isLoading } = useQuery({
    queryKey: ['reservations', 'me'],
    queryFn: () => reservationsApi.list({ limit: 200 }),
  })

  const filtered =
    filter === 'all'
      ? (reservations ?? [])
      : (reservations ?? []).filter((r) => r.status === filter)

  const countFor = (value) =>
    value === 'all'
      ? (reservations?.length ?? 0)
      : (reservations ?? []).filter((r) => r.status === value).length

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Mis reservas</h1>
        <p className="text-gray-500 mt-1">Historial completo de tus estancias</p>
      </div>

      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
              filter === f.value
                ? 'border-primary-600 text-primary-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {f.label}
            {!isLoading && (
              <span className="ml-1.5 text-xs bg-gray-100 text-gray-500 rounded-full px-1.5 py-0.5">
                {countFor(f.value)}
              </span>
            )}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500">No hay reservas para mostrar</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((r) => (
            <ReservationCard key={r.id} reservation={r} />
          ))}
        </div>
      )}
    </div>
  )
}
