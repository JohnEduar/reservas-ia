import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { accommodationsApi } from '../api/accommodations'
import CreateReservationModal from '../components/CreateReservationModal'
import Spinner from '../components/Spinner'

export default function AccommodationDetailPage() {
  const { id } = useParams()
  const [activeImg, setActiveImg] = useState(0)
  const [showModal, setShowModal] = useState(false)

  const { data: accommodation, isLoading, error } = useQuery({
    queryKey: ['accommodation', id],
    queryFn: () => accommodationsApi.get(id),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !accommodation) {
    return (
      <div className="text-center py-20">
        <p className="text-red-600 mb-4">No se pudo cargar el alojamiento</p>
        <Link to="/accommodations" className="text-primary-600 hover:underline">
          ← Volver al listado
        </Link>
      </div>
    )
  }

  const images = [...accommodation.images].sort((a, b) => {
    if (a.is_primary) return -1
    if (b.is_primary) return 1
    return a.sort_order - b.sort_order
  })

  return (
    <div className="max-w-4xl mx-auto">
      {showModal && (
        <CreateReservationModal
          accommodation={accommodation}
          onClose={() => setShowModal(false)}
        />
      )}

      <div className="mb-5">
        <Link to="/accommodations" className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
          ← Volver al listado
        </Link>
      </div>

      {/* Image gallery */}
      <div className="rounded-2xl overflow-hidden bg-gray-100 mb-6">
        {images.length > 0 ? (
          <div>
            <div className="aspect-[16/9] overflow-hidden">
              <img
                src={images[activeImg].url}
                alt={accommodation.title}
                className="w-full h-full object-cover"
              />
            </div>
            {images.length > 1 && (
              <div className="flex gap-2 p-3 bg-gray-50 overflow-x-auto">
                {images.map((img, i) => (
                  <button
                    key={img.id}
                    onClick={() => setActiveImg(i)}
                    className={`shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition-all ${
                      i === activeImg ? 'border-primary-500' : 'border-transparent opacity-60 hover:opacity-100'
                    }`}
                  >
                    <img src={img.url} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="aspect-[16/9] flex items-center justify-center">
            <span className="text-6xl">🏕️</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main info */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{accommodation.title}</h1>
            <p className="text-gray-500 mt-2 flex items-center gap-1">
              <span>📍</span> {accommodation.location}
            </p>
          </div>

          {accommodation.description && (
            <div>
              <h2 className="text-base font-semibold text-gray-900 mb-2">Descripción</h2>
              <p className="text-gray-600 leading-relaxed text-sm whitespace-pre-line">
                {accommodation.description}
              </p>
            </div>
          )}

          {accommodation.amenities.length > 0 && (
            <div>
              <h2 className="text-base font-semibold text-gray-900 mb-3">Comodidades</h2>
              <div className="flex flex-wrap gap-2">
                {accommodation.amenities.map((a) => (
                  <span
                    key={a.id}
                    className="flex items-center gap-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg px-3 py-1.5"
                  >
                    <span>{a.icon ?? '✓'}</span>
                    {a.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Booking card */}
        <div>
          <div className="bg-white rounded-2xl border border-gray-200 p-5 sticky top-6">
            <div className="mb-4">
              <span className="text-3xl font-bold text-gray-900">
                ${Number(accommodation.price_per_night).toLocaleString('es-ES')}
              </span>
              <span className="text-gray-400 text-sm"> / noche</span>
            </div>

            <div className="space-y-2 text-sm text-gray-600 mb-5">
              <div className="flex items-center gap-2">
                <span>👥</span>
                <span>Hasta {accommodation.max_guests} {accommodation.max_guests === 1 ? 'huésped' : 'huéspedes'}</span>
              </div>
            </div>

            <button
              onClick={() => setShowModal(true)}
              className="w-full py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl transition-colors text-sm shadow-sm shadow-primary-200"
            >
              Reservar ahora
            </button>

            <p className="text-xs text-gray-400 text-center mt-3">
              Sin cargos hasta confirmar
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
