import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { reservationsApi } from '../api/reservations'
import Spinner from './Spinner'

export default function CreateReservationModal({ onClose, accommodation }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    accommodation_id: accommodation?.id ?? '',
    check_in: '',
    check_out: '',
    guest_count: 1,
    notes: '',
  })
  const [errors, setErrors] = useState({})

  const mutation = useMutation({
    mutationFn: () =>
      reservationsApi.create({
        accommodation_id: Number(form.accommodation_id),
        check_in: form.check_in,
        check_out: form.check_out,
        guest_count: Number(form.guest_count),
        notes: form.notes || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations', 'me'] })
      onClose()
    },
  })

  useEffect(() => {
    const handleKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  const set = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }))
    setErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!form.accommodation_id || Number(form.accommodation_id) < 1)
      e.accommodation_id = 'Ingresa un ID de alojamiento válido'
    if (!form.check_in) e.check_in = 'Requerido'
    if (!form.check_out) e.check_out = 'Requerido'
    else if (form.check_in && form.check_out <= form.check_in)
      e.check_out = 'Debe ser posterior al check-in'
    if (!form.guest_count || Number(form.guest_count) < 1)
      e.guest_count = 'Mínimo 1 huésped'
    return e
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) return setErrors(errs)
    mutation.mutate()
  }

  const today = new Date().toISOString().split('T')[0]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Nueva reserva</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {accommodation ? (
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span className="text-xl">🏕️</span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{accommodation.title}</p>
                <p className="text-xs text-gray-500">{accommodation.location}</p>
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ID de alojamiento
              </label>
              <input
                type="number"
                min="1"
                placeholder="Ej. 1"
                value={form.accommodation_id}
                onChange={set('accommodation_id')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              {errors.accommodation_id && (
                <p className="text-xs text-red-600 mt-1">{errors.accommodation_id}</p>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Check-in</label>
              <input
                type="date"
                min={today}
                value={form.check_in}
                onChange={set('check_in')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              {errors.check_in && (
                <p className="text-xs text-red-600 mt-1">{errors.check_in}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Check-out</label>
              <input
                type="date"
                min={form.check_in || today}
                value={form.check_out}
                onChange={set('check_out')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              {errors.check_out && (
                <p className="text-xs text-red-600 mt-1">{errors.check_out}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Huéspedes</label>
            <input
              type="number"
              min="1"
              value={form.guest_count}
              onChange={set('guest_count')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            {errors.guest_count && (
              <p className="text-xs text-red-600 mt-1">{errors.guest_count}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notas <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <textarea
              rows={3}
              maxLength={1000}
              placeholder="Solicitudes especiales, horario de llegada..."
              value={form.notes}
              onChange={set('notes')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
            />
          </div>

          {mutation.isError && (
            <p className="text-sm text-red-600">
              {mutation.error?.response?.data?.detail || 'Error al crear la reserva'}
            </p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              disabled={mutation.isPending}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {mutation.isPending && <Spinner size="sm" />}
              Confirmar reserva
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
