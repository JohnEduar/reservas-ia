import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../../api/admin'
import Spinner from '../../components/Spinner'
import StatusBadge from '../../components/StatusBadge'

const TABS = [
  { label: 'Todas', value: undefined },
  { label: 'Confirmadas', value: 'confirmed' },
  { label: 'Canceladas', value: 'cancelled' },
]

function fmtDate(d) {
  if (!d) return '–'
  return new Date(d + 'T00:00:00').toLocaleDateString('es-CO')
}

function fmtPrice(n) {
  if (n === undefined || n === null) return '–'
  return Number(n).toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })
}

export default function AdminReservationsPage() {
  const [statusFilter, setStatusFilter] = useState(undefined)

  const { data: reservations, isLoading } = useQuery({
    queryKey: ['admin', 'reservations', statusFilter],
    queryFn: () =>
      adminApi.reservations({
        limit: 200,
        ...(statusFilter ? { status: statusFilter } : {}),
      }),
  })

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reservas</h1>
        <p className="text-gray-500 mt-1">
          {isLoading ? '…' : `${reservations?.length ?? 0} reservas`}
        </p>
      </div>

      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {TABS.map((tab) => (
          <button
            key={String(tab.value)}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              statusFilter === tab.value
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden overflow-x-auto">
          <table className="w-full text-sm min-w-[720px]">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-gray-600 font-medium">ID</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Alojamiento</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Huésped</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Check-in</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Check-out</th>
                <th className="text-center px-4 py-3 text-gray-600 font-medium">Estado</th>
                <th className="text-right px-4 py-3 text-gray-600 font-medium">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reservations?.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs">{r.id}</td>
                  <td className="px-4 py-3 text-gray-800 max-w-[180px]">
                    <span className="block truncate">{r.accommodation_title}</span>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-gray-800">
                      {r.guest_name || <span className="text-gray-400">–</span>}
                    </p>
                    <p className="text-xs text-gray-400">{r.guest_email}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{fmtDate(r.check_in)}</td>
                  <td className="px-4 py-3 text-gray-600">{fmtDate(r.check_out)}</td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-gray-800">
                    {fmtPrice(r.total_price)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {reservations?.length === 0 && (
            <div className="p-8 text-center text-gray-400 text-sm">No hay reservas</div>
          )}
        </div>
      )}
    </div>
  )
}
