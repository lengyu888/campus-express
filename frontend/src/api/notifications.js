import http from './http'

export const listNotifications = (params) => http.get('/notifications', { params })
export const unreadCount = () => http.get('/notifications/unread-count')
export const markRead = (id) => http.patch(`/notifications/${id}/read`)
export const markAllRead = () => http.post('/notifications/read-all')

export const listAnnouncements = (params) => http.get('/announcements', { params })
export const createAnnouncement = (payload) => http.post('/announcements', payload)
export const updateAnnouncement = (id, payload) => http.put(`/announcements/${id}`, payload)
export const deleteAnnouncement = (id) => http.delete(`/announcements/${id}`)
