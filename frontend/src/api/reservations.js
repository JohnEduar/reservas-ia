import api from '../lib/axios'

export const reservationsApi = {
  list: (params) => api.get('/reservations/me', { params }).then((r) => r.data),
  get: (id) => api.get(`/reservations/${id}`).then((r) => r.data),
  create: (data) => api.post('/reservations/', data).then((r) => r.data),
  cancel: (id) => api.post(`/reservations/${id}/cancel`).then((r) => r.data),
}
