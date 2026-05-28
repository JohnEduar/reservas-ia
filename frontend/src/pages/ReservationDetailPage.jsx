import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reservationsApi } from '../api/reservations'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'

function formatDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('es-ES', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function nightCount(checkIn, checkOut) {
  const d1 = new Date(checkIn)
  const d2 = new Date(checkOut)
  return Math.round((d2 - d1) / (1000 * 60 * 60 * 24))
}

export default function ReservationDetailPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const [confirmCancel, setConfirmCancel] = useState(false)

  const { data: reservation, isLoading, error } = useQuery({
    queryKey: ['reservation', id],
    queryFn: () => reservationsApi.get(id),
  })

  const cancelMutation = useMutation({
    mutationFn: () => reservationsApi.cancel(id),
    onSuccess: (updated) => {
      queryClient.setQueryData(['reservation', id], updated)
      queryClient.invalidateQueries({ queryKey: ['reservations', 'me'] })
      setConfirmCancel(false)
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600 mb-4">No se pudo cargar la reserva</p>
        <Link to="/reservations" className="text-primary-600 hover:underline">
          ← Volver a mis reservas
        </Link>
      </div>
    )
  }

  const nights = nightCount(reservation.check_in, reservation.check_out)
  const isActive = reservation.status === 'confirmed'
  const isFuture = new Date(reservation.check_in) > new Date()

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <Link to="/reservations" className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
          ← Volver a mis reservas
        </Link>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 p-6 text-white">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-primary-100 text-sm">Reserva</p>
              <h1 className="text-2xl font-bold">#{reservation.id}</h1>
              <p className="text-primary-100 mt-1">Alojamiento #{reservation.accommodation_id}</p>
            </div>
            <StatusBadge status={reservation.status} />
          </div>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Check-in</p>
              <p className="font-medium text-gray-900 capitalize">{formatDate(reservation.check_in)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Check-out</p>
              <p className="font-medium text-gray-900 capitalize">{formatDate(reservation.check_out)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Duración</p>
              <p className="font-medium text-gray-900">
                {nights} {nights === 1 ? 'noche' : 'noches'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Huéspedes</p>
              <p className="font-medium text-gray-900">{reservation.guest_count}</p>
            </div>
          </div>

          <div className="border-t border-gray-100 pt-6">
            <div className="flex justify-between items-center">
              <p className="text-gray-600">Total pagado</p>
              <p className="text-2xl font-bold text-gray-900">
                ${Number(reservation.total_price).toLocaleString('es-ES', {
                  minimumFractionDigits: 2,
                })}
              </p>
            </div>
          </div>

          {reservation.notes && (
            <div className="border-t border-gray-100 pt-6">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Notas</p>
              <p className="text-gray-700 text-sm">{reservation.notes}</p>
            </div>
          )}

          <div className="border-t border-gray-100 pt-6 text-xs text-gray-400 space-y-1">
            <p>Creada: {new Date(reservation.created_at).toLocaleString('es-ES')}</p>
            <p>Actualizada: {new Date(reservation.updated_at).toLocaleString('es-ES')}</p>
          </div>

          {isActive && isFuture && (
            <div className="border-t border-gray-100 pt-6">
              {cancelMutation.isError && (
                <p className="text-sm text-red-600 mb-3">
                  {cancelMutation.error?.response?.data?.detail || 'Error al cancelar la reserva'}
                </p>
              )}
              {!confirmCancel ? (
                <button
                  onClick={() => setConfirmCancel(true)}
                  className="px-4 py-2 text-sm font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                >
                  Cancelar reserva
                </button>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                  <p className="text-sm text-red-800 font-medium mb-3">
                    ¿Confirmas la cancelación? Esta acción no se puede deshacer.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => cancelMutation.mutate()}
                      disabled={cancelMutation.isPending}
                      className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                    >
                      {cancelMutation.isPending && <Spinner size="sm" />}
                      Sí, cancelar
                    </button>
                    <button
                      onClick={() => setConfirmCancel(false)}
                      disabled={cancelMutation.isPending}
                      className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      Volver
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
