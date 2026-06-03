import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '../../api/admin'
import { accommodationsApi } from '../../api/accommodations'
import { amenitiesApi } from '../../api/accommodations'
import Spinner from '../../components/Spinner'

const EMPTY_FORM = {
  title: '',
  description: '',
  location: '',
  price_per_night: '',
  max_guests: 1,
  amenity_ids: [],
}

function AccommodationModal({ accommodation, onClose }) {
  const queryClient = useQueryClient()
  const isEdit = !!accommodation

  const [form, setForm] = useState(
    isEdit
      ? {
          title: accommodation.title,
          description: accommodation.description ?? '',
          location: accommodation.location,
          price_per_night: accommodation.price_per_night,
          max_guests: accommodation.max_guests,
          amenity_ids: accommodation.amenities?.map((a) => a.id) ?? [],
        }
      : EMPTY_FORM,
  )
  const [errors, setErrors] = useState({})

  const { data: amenities = [] } = useQuery({
    queryKey: ['amenities'],
    queryFn: amenitiesApi.list,
  })

  const mutation = useMutation({
    mutationFn: () => {
      const payload = {
        ...form,
        price_per_night: Number(form.price_per_night),
        max_guests: Number(form.max_guests),
        amenity_ids: form.amenity_ids,
      }
      return isEdit
        ? accommodationsApi.update(accommodation.id, payload)
        : accommodationsApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'accommodations'] })
      onClose()
    },
  })

  useEffect(() => {
    const handleKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  const set = (field) => (e) => {
    setForm((p) => ({ ...p, [field]: e.target.value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const toggleAmenity = (id) => {
    setForm((p) => ({
      ...p,
      amenity_ids: p.amenity_ids.includes(id)
        ? p.amenity_ids.filter((x) => x !== id)
        : [...p.amenity_ids, id],
    }))
  }

  const validate = () => {
    const e = {}
    if (!form.title.trim() || form.title.length < 5) e.title = 'Mínimo 5 caracteres'
    if (!form.location.trim() || form.location.length < 3) e.location = 'Mínimo 3 caracteres'
    if (!form.price_per_night || Number(form.price_per_night) <= 0)
      e.price_per_night = 'Debe ser mayor a 0'
    if (!form.max_guests || Number(form.max_guests) < 1 || Number(form.max_guests) > 50)
      e.max_guests = 'Entre 1 y 50'
    return e
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) return setErrors(errs)
    mutation.mutate()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
          <h2 className="text-lg font-semibold text-gray-900">
            {isEdit ? 'Editar alojamiento' : 'Nuevo alojamiento'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="overflow-y-auto p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
            <input
              type="text"
              maxLength={255}
              placeholder="Cabaña en el bosque..."
              value={form.title}
              onChange={set('title')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            {errors.title && <p className="text-xs text-red-600 mt-1">{errors.title}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ubicación</label>
            <input
              type="text"
              maxLength={255}
              placeholder="Medellín, Antioquia"
              value={form.location}
              onChange={set('location')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            {errors.location && <p className="text-xs text-red-600 mt-1">{errors.location}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Precio / noche
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                placeholder="150000"
                value={form.price_per_night}
                onChange={set('price_per_night')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              {errors.price_per_night && (
                <p className="text-xs text-red-600 mt-1">{errors.price_per_night}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Capacidad máx.
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={form.max_guests}
                onChange={set('max_guests')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              {errors.max_guests && (
                <p className="text-xs text-red-600 mt-1">{errors.max_guests}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <textarea
              rows={3}
              maxLength={2000}
              placeholder="Describe el alojamiento..."
              value={form.description}
              onChange={set('description')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
            />
          </div>

          {amenities.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Comodidades <span className="text-gray-400 font-normal">(opcional)</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {amenities.map((a) => {
                  const selected = form.amenity_ids.includes(a.id)
                  return (
                    <button
                      key={a.id}
                      type="button"
                      onClick={() => toggleAmenity(a.id)}
                      className={`flex items-center gap-1.5 text-sm rounded-lg px-3 py-1.5 border transition-colors ${
                        selected
                          ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
                          : 'border-gray-200 text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      {a.icon && <span>{a.icon}</span>}
                      {a.name}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {mutation.isError && (
            <p className="text-sm text-red-600">
              {mutation.error?.response?.data?.detail || 'Error al guardar'}
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
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {mutation.isPending && <Spinner size="sm" />}
              {isEdit ? 'Guardar cambios' : 'Crear alojamiento'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function AdminAccommodationsPage() {
  const queryClient = useQueryClient()
  const [modal, setModal] = useState(null) // null | 'create' | accommodation object

  const { data: accommodations, isLoading } = useQuery({
    queryKey: ['admin', 'accommodations'],
    queryFn: () => adminApi.accommodations({ limit: 200 }),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }) => accommodationsApi.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'accommodations'] }),
  })

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alojamientos</h1>
          <p className="text-gray-500 mt-1">
            {isLoading ? '…' : `${accommodations?.length ?? 0} alojamientos`}
          </p>
        </div>
        <button
          onClick={() => setModal('create')}
          className="shrink-0 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          + Nuevo alojamiento
        </button>
      </div>

      {modal && (
        <AccommodationModal
          accommodation={modal === 'create' ? null : modal}
          onClose={() => setModal(null)}
        />
      )}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden overflow-x-auto">
          <table className="w-full text-sm min-w-[700px]">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-gray-600 font-medium">ID</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Título</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Ubicación</th>
                <th className="text-right px-4 py-3 text-gray-600 font-medium">Precio/noche</th>
                <th className="text-center px-4 py-3 text-gray-600 font-medium">Capacidad</th>
                <th className="text-center px-4 py-3 text-gray-600 font-medium">Estado</th>
                <th className="text-right px-4 py-3 text-gray-600 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {accommodations?.map((a) => (
                <tr key={a.id} className={`hover:bg-gray-50 ${!a.is_active ? 'opacity-50' : ''}`}>
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs">{a.id}</td>
                  <td className="px-4 py-3 text-gray-800 max-w-[220px]">
                    <span className="block truncate font-medium">{a.title}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 max-w-[160px]">
                    <span className="block truncate">{a.location}</span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-700 font-medium">
                    ${Number(a.price_per_night).toLocaleString('es-CO')}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-600">
                    {a.max_guests} {a.max_guests === 1 ? 'huésped' : 'huéspedes'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        a.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {a.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setModal(a)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
                      >
                        Editar
                      </button>
                      <span className="text-gray-200">|</span>
                      <button
                        onClick={() => toggleMutation.mutate({ id: a.id, is_active: !a.is_active })}
                        disabled={toggleMutation.isPending}
                        className={`text-xs font-medium transition-colors disabled:opacity-50 ${
                          a.is_active
                            ? 'text-red-500 hover:text-red-700'
                            : 'text-green-600 hover:text-green-800'
                        }`}
                      >
                        {a.is_active ? 'Desactivar' : 'Activar'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {accommodations?.length === 0 && (
            <div className="p-12 text-center text-gray-400 text-sm">
              No hay alojamientos. Crea el primero con el botón de arriba.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
