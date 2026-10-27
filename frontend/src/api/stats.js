import http from './http'

export const statsOverview = (params) => http.get('/stats/overview', { params })
export const packageTrend = (params) => http.get('/stats/packages/trend', { params })
export const stationWorkload = () => http.get('/stats/stations/workload')
export const overdueStats = () => http.get('/stats/overdue')
