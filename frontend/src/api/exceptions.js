import http from './http'

export const listExceptions = (params) => http.get('/exceptions', { params })
export const exceptionSummary = () => http.get('/exceptions/summary')
export const handleException = (id, payload) => http.patch(`/exceptions/${id}`, payload)
