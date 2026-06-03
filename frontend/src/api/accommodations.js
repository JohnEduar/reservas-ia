import api from '../lib/axios'

export const accommodationsApi = {
  list: (params) => api.get('/accommodations/', { params }).then((r) => r.data),
  get: (id) => api.get(`/accommodations/${id}`).then((r) => r.data),
  create: (data) => api.post('/accommodations/', data).then((r) => r.data),
  update: (id, data) => api.put(`/accommodations/${id}`, data).then((r) => r.data),
}

export const amenitiesApi = {
  list: () => api.get('/amenities/').then((r) => r.data),
}
