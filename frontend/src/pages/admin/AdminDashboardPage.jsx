import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../../api/admin'
import Spinner from '../../components/Spinner'
import StatusBadge from '../../components/StatusBadge'

const currentYear = new Date().getFullYear()

function KPICard({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-sm font-medium text-gray-700 mt-1">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

function fmt(n) {
  if (n === undefined || n === null) return '–'
  return Number(n).toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })
}

function fmtDate(d) {
  if (!d) return '–'
  return new Date(d + 'T00:00:00').toLocaleDateString('es-CO')
}

export default function AdminDashboardPage() {
  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['admin', 'kpis'],
    queryFn: adminApi.kpis,
  })

  const { data: revenue, isLoading: revenueLoading } = useQuery({
    queryKey: ['admin', 'revenue', 'period', currentYear],
    queryFn: () => adminApi.revenueByPeriod({ year: currentYear }),
  })

  const { data: activity, isLoading: activityLoading } = useQuery({
    queryKey: ['admin', 'activity'],
    queryFn: () => adminApi.activityReport({ limit: 5 }),
  })

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Métricas y analíticas</h1>
        <p className="text-gray-500 mt-1">Panel administrativo de GlampBook</p>
      </div>

      {kpisLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-10">
          <KPICard
            label="Usuarios totales"
            value={kpis?.total_users ?? '–'}
            sub={`${kpis?.active_users ?? '–'} activos`}
          />
          <KPICard
            label="Alojamientos"
            value={kpis?.active_accommodations ?? '–'}
            sub={`de ${kpis?.total_accommodations ?? '–'} registrados`}
          />
          <KPICard
            label="Reservas totales"
            value={kpis?.total_reservations ?? '–'}
            sub={`${kpis?.confirmed_reservations ?? '–'} confirmadas`}
          />
          <KPICard
            label="Canceladas"
            value={kpis?.cancelled_reservations ?? '–'}
            color="text-red-600"
          />
          <KPICard
            label="Ingresos totales"
            value={fmt(kpis?.total_revenue)}
            color="text-green-700"
          />
          <KPICard
            label="Ingresos este mes"
            value={fmt(kpis?.revenue_this_month)}
            color="text-green-700"
            sub={`${kpis?.reservations_this_month ?? '–'} reservas`}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Ingresos por mes ({currentYear})
          </h2>
          {revenueLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : !revenue?.length ? (
            <div className="bg-white rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-400">
              Sin datos para {currentYear}
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-4 py-3 text-gray-600 font-medium">Período</th>
                    <th className="text-right px-4 py-3 text-gray-600 font-medium">Reservas</th>
                    <th className="text-right px-4 py-3 text-gray-600 font-medium">Ingresos</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {revenue.map((row) => (
                    <tr key={row.period} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-700">{row.period}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{row.reservations_count}</td>
                      <td className="px-4 py-3 text-right font-medium text-green-700">
                        {fmt(row.revenue)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Actividad reciente</h2>
          {activityLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 text-sm font-medium text-gray-700">
                  Últimas reservas
                </div>
                {activity?.recent_reservations?.length === 0 ? (
                  <p className="px-4 py-3 text-sm text-gray-400">Sin reservas recientes</p>
                ) : (
                  activity?.recent_reservations?.slice(0, 4).map((r) => (
                    <div
                      key={r.id}
                      className="px-4 py-3 flex items-center justify-between border-b border-gray-50 last:border-0"
                    >
                      <div className="min-w-0 mr-3">
                        <p className="text-sm font-medium text-gray-800 truncate">
                          {r.accommodation_title}
                        </p>
                        <p className="text-xs text-gray-400 truncate">
                          {r.guest_email} · {fmtDate(r.check_in)} – {fmtDate(r.check_out)}
                        </p>
                      </div>
                      <StatusBadge status={r.status} />
                    </div>
                  ))
                )}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 text-sm font-medium text-gray-700">
                  Nuevos usuarios
                </div>
                {activity?.recent_registrations?.length === 0 ? (
                  <p className="px-4 py-3 text-sm text-gray-400">Sin registros recientes</p>
                ) : (
                  activity?.recent_registrations?.slice(0, 4).map((u) => (
                    <div
                      key={u.id}
                      className="px-4 py-3 flex items-center justify-between border-b border-gray-50 last:border-0"
                    >
                      <div className="min-w-0 mr-3">
                        <p className="text-sm font-medium text-gray-800">
                          {u.full_name || <span className="text-gray-400 italic">sin nombre</span>}
                        </p>
                        <p className="text-xs text-gray-400 truncate">{u.email}</p>
                      </div>
                      <span className="text-xs text-gray-400 shrink-0">
                        {u.created_at
                          ? new Date(u.created_at).toLocaleDateString('es-CO')
                          : ''}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
