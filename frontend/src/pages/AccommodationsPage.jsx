import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { accommodationsApi } from '../api/accommodations'
import Spinner from '../components/Spinner'

function AccommodationCard({ accommodation }) {
  const primary = accommodation.images.find((i) => i.is_primary) ?? accommodation.images[0]

  return (
    <Link
      to={`/accommodations/${accommodation.id}`}
      className="group bg-white rounded-2xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
    >
      <div className="aspect-[4/3] bg-gray-100 overflow-hidden">
        {primary ? (
          <img
            src={primary.url}
            alt={accommodation.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-4xl">🏕️</span>
          </div>
        )}
      </div>
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="font-semibold text-gray-900 leading-snug line-clamp-1 group-hover:text-primary-700 transition-colors">
            {accommodation.title}
          </h3>
          <span className="shrink-0 text-sm font-bold text-primary-700">
            ${Number(accommodation.price_per_night).toLocaleString('es-ES')}
            <span className="text-xs font-normal text-gray-400">/noche</span>
          </span>
        </div>
        <p className="text-sm text-gray-500 mb-3 flex items-center gap-1">
          <span>📍</span> {accommodation.location}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">
            Hasta {accommodation.max_guests} {accommodation.max_guests === 1 ? 'huésped' : 'huéspedes'}
          </span>
          {accommodation.amenities.length > 0 && (
            <div className="flex gap-1">
              {accommodation.amenities.slice(0, 3).map((a) => (
                <span
                  key={a.id}
                  title={a.name}
                  className="text-sm bg-gray-100 rounded-md px-1.5 py-0.5"
                >
                  {a.icon ?? '✓'}
                </span>
              ))}
              {accommodation.amenities.length > 3 && (
                <span className="text-xs text-gray-400 self-center">
                  +{accommodation.amenities.length - 3}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

function FilterBar({ filters, onChange }) {
  const [local, setLocal] = useState(filters)

  const set = (field) => (e) =>
    setLocal((p) => ({ ...p, [field]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    onChange(local)
  }

  const handleReset = () => {
    const empty = { location: '', min_guests: '', min_price: '', max_price: '' }
    setLocal(empty)
    onChange(empty)
  }

  const hasFilters = Object.values(filters).some(Boolean)

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-2xl border border-gray-200 p-4 mb-6 flex flex-wrap gap-3 items-end"
    >
      <div className="flex-1 min-w-[180px]">
        <label className="block text-xs font-medium text-gray-500 mb-1">Ubicación</label>
        <input
          type="text"
          placeholder="Ciudad, región..."
          value={local.location}
          onChange={set('location')}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-gray-50"
        />
      </div>
      <div className="w-32">
        <label className="block text-xs font-medium text-gray-500 mb-1">Huéspedes</label>
        <input
          type="number"
          min="1"
          placeholder="1"
          value={local.min_guests}
          onChange={set('min_guests')}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-gray-50"
        />
      </div>
      <div className="w-28">
        <label className="block text-xs font-medium text-gray-500 mb-1">Precio mín.</label>
        <input
          type="number"
          min="0"
          placeholder="$0"
          value={local.min_price}
          onChange={set('min_price')}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-gray-50"
        />
      </div>
      <div className="w-28">
        <label className="block text-xs font-medium text-gray-500 mb-1">Precio máx.</label>
        <input
          type="number"
          min="0"
          placeholder="$∞"
          value={local.max_price}
          onChange={set('max_price')}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-gray-50"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Buscar
        </button>
        {hasFilters && (
          <button
            type="button"
            onClick={handleReset}
            className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-lg transition-colors"
          >
            Limpiar
          </button>
        )}
      </div>
    </form>
  )
}

const EMPTY_FILTERS = { location: '', min_guests: '', min_price: '', max_price: '' }

export default function AccommodationsPage() {
  const [filters, setFilters] = useState(EMPTY_FILTERS)

  const queryParams = {
    ...(filters.location && { location: filters.location }),
    ...(filters.min_guests && { min_guests: Number(filters.min_guests) }),
    ...(filters.min_price && { min_price: Number(filters.min_price) }),
    ...(filters.max_price && { max_price: Number(filters.max_price) }),
    limit: 50,
  }

  const { data: accommodations, isLoading } = useQuery({
    queryKey: ['accommodations', queryParams],
    queryFn: () => accommodationsApi.list(queryParams),
    staleTime: 0,
  })

  const handleFilters = useCallback((f) => setFilters(f), [])

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Alojamientos</h1>
        <p className="text-gray-500 mt-1">Encuentra tu próxima escapada</p>
      </div>

      <FilterBar filters={filters} onChange={handleFilters} />

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : !accommodations?.length ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 p-16 text-center">
          <p className="text-gray-500 mb-1">No se encontraron alojamientos</p>
          <p className="text-sm text-gray-400">Prueba ajustando los filtros</p>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-400 mb-4">
            {accommodations.length} {accommodations.length === 1 ? 'alojamiento' : 'alojamientos'} encontrados
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {accommodations.map((a) => (
              <AccommodationCard key={a.id} accommodation={a} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
