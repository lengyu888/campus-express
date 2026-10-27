import http from './http'

export const listUsers = (params) => http.get('/users', { params })
export const createUser = (payload) => http.post('/users', payload)
export const updateUser = (id, payload) => http.put(`/users/${id}`, payload)
export const updateUserStatus = (id, status) => http.patch(`/users/${id}/status`, { status })
