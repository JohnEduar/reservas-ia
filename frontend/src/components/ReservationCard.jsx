import { Link } from 'react-router-dom'
import StatusBadge from './StatusBadge'

function formatDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function nightCount(checkIn, checkOut) {
  const d1 = new Date(checkIn)
  const d2 = new Date(checkOut)
  return Math.round((d2 - d1) / (1000 * 60 * 60 * 24))
}

export default function ReservationCard({ reservation }) {
  const nights = nightCount(reservation.check_in, reservation.check_out)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-medium text-gray-900">Reserva #{reservation.id}</span>
            <StatusBadge status={reservation.status} />
          </div>
          <p className="text-sm text-gray-500">Alojamiento #{reservation.accommodation_id}</p>
        </div>
        <Link
          to={`/reservations/${reservation.id}`}
          className="text-sm text-primary-600 hover:text-primary-800 font-medium shrink-0"
        >
          Ver detalle →
        </Link>
      </div>
      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <div>
          <p className="text-gray-400 text-xs uppercase tracking-wide">Check-in</p>
          <p className="font-medium text-gray-700">{formatDate(reservation.check_in)}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs uppercase tracking-wide">Check-out</p>
          <p className="font-medium text-gray-700">{formatDate(reservation.check_out)}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs uppercase tracking-wide">Noches</p>
          <p className="font-medium text-gray-700">{nights}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs uppercase tracking-wide">Total</p>
          <p className="font-medium text-gray-700">
            ${Number(reservation.total_price).toLocaleString('es-ES', { minimumFractionDigits: 2 })}
          </p>
        </div>
      </div>
    </div>
  )
}
