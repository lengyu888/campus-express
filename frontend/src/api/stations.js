import http from './http'

export const listStations = (params) => http.get('/stations', { params })
export const createStation = (payload) => http.post('/stations', payload)
export const updateStation = (id, payload) => http.put(`/stations/${id}`, payload)
export const updateStationStatus = (id, status) => http.patch(`/stations/${id}/status`, { status })

export const listShelves = (stationId) => http.get(`/stations/${stationId}/shelves`)
export const createShelf = (stationId, payload) => http.post(`/stations/${stationId}/shelves`, payload)
export const updateShelf = (id, payload) => http.put(`/shelves/${id}`, payload)
export const deleteShelf = (id) => http.delete(`/shelves/${id}`)
