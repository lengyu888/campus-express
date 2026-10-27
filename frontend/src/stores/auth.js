import { defineStore } from 'pinia'
import { login as apiLogin, logout as apiLogout, fetchMe } from '../api/auth'
import { tokenStore } from '../api/http'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loading: false
  }),
  getters: {
    isLoggedIn: () => Boolean(tokenStore.access),
    role: (state) => state.user?.role || '',
    roleLabel: (state) => {
      const map = { student: '学生', staff: '驿站工作人员', admin: '系统管理员' }
      return map[state.user?.role] || '访客'
    }
  },
  actions: {
    async login(payload) {
      this.loading = true
      try {
        const data = await apiLogin(payload)
        tokenStore.set(data.access_token, data.refresh_token)
        this.user = data.user
        return data
      } finally {
        this.loading = false
      }
    },
    async loadMe() {
      if (!tokenStore.access) return null
      this.user = await fetchMe()
      return this.user
    },
    async logout() {
      try {
        await apiLogout()
      } catch (e) {
        // 令牌可能已过期，忽略服务端异常，前端照常清理
      }
      tokenStore.clear()
      this.user = null
    },
    hasRole(...roles) {
      return roles.includes(this.user?.role)
    }
  }
})
