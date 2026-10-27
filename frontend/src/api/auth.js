import http from './http'

export const login = (payload) => http.post('/auth/login', payload)
export const logout = () => http.post('/auth/logout')
export const fetchMe = () => http.get('/auth/me')
export const changePassword = (payload) => http.put('/auth/password', payload)
export const register = (payload) => http.post('/auth/register', payload)
