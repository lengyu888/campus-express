import axios from 'axios'
import { ElMessage } from 'element-plus'

const ACCESS_KEY = 'ce_access_token'
const REFRESH_KEY = 'ce_refresh_token'

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY) || ''
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY) || ''
  },
  set(access, refresh) {
    localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  }
}

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 15000
})

http.interceptors.request.use((config) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = null

async function refreshToken() {
  const token = tokenStore.refresh
  if (!token) throw new Error('登录已过期')
  const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: token })
  if (data.code !== 0) throw new Error(data.message || '登录已过期')
  tokenStore.set(data.data.access_token, data.data.refresh_token)
  return data.data.access_token
}

http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body.code !== 'undefined') {
      if (body.code !== 0) {
        ElMessage.error(body.message || '请求失败')
        return Promise.reject(new Error(body.message || '请求失败'))
      }
      return body.data
    }
    return body
  },
  async (error) => {
    const { response, config } = error
    if (response?.status === 401 && !config._retried) {
      config._retried = true
      try {
        refreshing = refreshing || refreshToken()
        const access = await refreshing
        refreshing = null
        config.headers.Authorization = `Bearer ${access}`
        return http(config)
      } catch (e) {
        refreshing = null
        tokenStore.clear()
        if (!location.pathname.startsWith('/login')) {
          location.href = `/login?redirect=${encodeURIComponent(location.pathname)}`
        }
        return Promise.reject(e)
      }
    }

    const message = response?.data?.message || error.message || '网络异常'
    ElMessage.error(message)
    return Promise.reject(new Error(message))
  }
)

export default http
