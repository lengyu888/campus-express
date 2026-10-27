import http from './http'

export const listPackages = (params) => http.get('/packages', { params })
export const packagesSummary = (params) => http.get('/packages/summary', { params })
export const getPackage = (id) => http.get(`/packages/${id}`)
export const getPackageByCode = (code, params) => http.get(`/packages/by-code/${code}`, { params })
export const trackPackage = (trackingNo) => http.get(`/packages/track/${trackingNo}`)

export const createPackage = (payload) => http.post('/packages', payload)
export const batchCreatePackages = (payload) => http.post('/packages/batch', payload)
export const movePackageShelf = (id, shelfId) => http.post(`/packages/${id}/shelf`, { shelf_id: shelfId })
export const pickupPackage = (id, payload) => http.post(`/packages/${id}/pickup`, payload)
export const returnPackage = (id, reason) => http.post(`/packages/${id}/return`, { reason })
export const markPackageException = (id, payload) => http.post(`/packages/${id}/exception`, payload)

export const listPickupRecords = (params) => http.get('/pickup-records', { params })
