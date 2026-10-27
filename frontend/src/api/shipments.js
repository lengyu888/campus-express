import http from './http'

export const listShipments = (params) => http.get('/shipments', { params })
export const shipmentsSummary = (params) => http.get('/shipments/summary', { params })
export const getShipment = (id) => http.get(`/shipments/${id}`)
export const createShipment = (payload) => http.post('/shipments', payload)
export const acceptShipment = (id, payload) => http.post(`/shipments/${id}/accept`, payload)
export const shipShipment = (id) => http.post(`/shipments/${id}/ship`)
export const completeShipment = (id) => http.post(`/shipments/${id}/complete`)
export const cancelShipment = (id) => http.post(`/shipments/${id}/cancel`)
export const getShipmentTracks = (id) => http.get(`/shipments/${id}/tracks`)
