import api from '../lib/axios'

export const usersApi = {
  me: () => api.get('/users/me').then((r) => r.data),
  update: (data) => api.put('/users/me', data).then((r) => r.data),
}
