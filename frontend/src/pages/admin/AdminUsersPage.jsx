import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../../api/admin'
import Spinner from '../../components/Spinner'

export default function AdminUsersPage() {
  const { data: users, isLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminApi.listUsers({ limit: 200 }),
  })

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Usuarios</h1>
        <p className="text-gray-500 mt-1">
          {isLoading ? '…' : `${users?.length ?? 0} usuarios registrados`}
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden overflow-x-auto">
          <table className="w-full text-sm min-w-[600px]">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-gray-600 font-medium">ID</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Nombre</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Email</th>
                <th className="text-center px-4 py-3 text-gray-600 font-medium">Estado</th>
                <th className="text-center px-4 py-3 text-gray-600 font-medium">Rol</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Registro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users?.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs">{u.id}</td>
                  <td className="px-4 py-3 text-gray-800">
                    {u.full_name || <span className="text-gray-400 italic">sin nombre</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{u.email}</td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        u.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {u.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {u.is_superuser ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                        Admin
                      </span>
                    ) : (
                      <span className="text-gray-400 text-xs">Huésped</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString('es-CO') : '–'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {users?.length === 0 && (
            <div className="p-8 text-center text-gray-400 text-sm">No hay usuarios</div>
          )}
        </div>
      )}
    </div>
  )
}
