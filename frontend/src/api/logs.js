import http from './http'

export const listLogs = (params) => http.get('/logs', { params })
export const logSummary = () => http.get('/logs/summary')
