import api from '../lib/axios'

export const adminApi = {
  kpis: () => api.get('/admin/kpis').then((r) => r.data),
  occupancy: (params) => api.get('/admin/stats/occupancy', { params }).then((r) => r.data),
  revenueByPeriod: (params) => api.get('/admin/stats/revenue/period', { params }).then((r) => r.data),
  revenueByAccommodation: (params) =>
    api.get('/admin/stats/revenue/accommodation', { params }).then((r) => r.data),
  reservations: (params) => api.get('/admin/reservations', { params }).then((r) => r.data),
  accommodations: (params) => api.get('/admin/accommodations', { params }).then((r) => r.data),
  activityReport: (params) => api.get('/admin/reports/activity', { params }).then((r) => r.data),
  listUsers: (params) => api.get('/users/', { params }).then((r) => r.data),
}
