<template>
  <div class="shell">
    <div class="route-progress" :class="{ active: routeLoading }"><span></span></div>

    <aside class="sidebar">
      <div class="brand">
        <div class="app-icon">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 8.5 12 3 3 8.5v7L12 21l9-5.5z" />
            <path d="M3 8.5 12 14l9-5.5M12 14v7" />
          </svg>
        </div>
        <div class="brand-text">
          <strong>校园快递</strong>
          <span>Campus Express</span>
        </div>
      </div>

      <nav class="nav" :style="{ '--idx': activeIndex }">
        <span class="nav-pill" aria-hidden="true"></span>
        <button
          v-for="item in menus"
          :key="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
          type="button"
          @click="router.push(item.path)"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="side-foot">
        <div class="side-note">
          <span class="dot"></span>
          <div>
            <strong>阶段一</strong>
            <span>认证与用户管理</span>
          </div>
        </div>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="topbar-left">
          <span class="today">{{ today }}</span>
          <span class="status-chip"><i></i> 服务正常</span>
        </div>
        <div class="topbar-right">
          <button
            class="icon-btn"
            type="button"
            :title="motionTier === 'reduced' ? '开启完整动效' : '切换到精简动效'"
            :aria-pressed="motionTier === 'reduced'"
            @click="toggleMotion"
          >
            <el-icon :size="18"><MagicStick /></el-icon>
            <span class="motion-dot" :class="{ off: motionTier === 'reduced' }"></span>
          </button>
          <button class="icon-btn" type="button" title="消息" aria-label="消息">
            <el-icon :size="18"><Bell /></el-icon>
            <span class="badge"></span>
          </button>
          <el-dropdown trigger="click" @command="onCommand">
            <div class="user-chip">
              <div class="avatar">{{ (auth.user?.name || '?').slice(0, 1) }}</div>
              <div class="user-meta">
                <strong>{{ auth.user?.name || '-' }}</strong>
                <span>{{ auth.user?.student_no || auth.roleLabel }}</span>
              </div>
              <el-icon class="chevron" :size="12"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <transition :name="transitionName" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <transition name="fab">
      <button v-if="showTop" class="back-top" type="button" aria-label="回到顶部" @click="scrollToTop">
        <el-icon :size="18"><ArrowUp /></el-icon>
      </button>
    </transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  HomeFilled, UserFilled, Setting, Bell, ArrowDown, ArrowUp, MagicStick
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { motionTier, toggleMotion } from '../motion'
import { routeLoading } from '../composables/routeProgress'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const menus = computed(() => {
  const items = [{ path: '/dashboard', label: '工作台', icon: HomeFilled }]
  if (auth.role === 'admin') items.push({ path: '/users', label: '用户管理', icon: UserFilled })
  items.push({ path: '/profile', label: '个人中心', icon: Setting })
  return items
})

const activeIndex = computed(() => {
  const idx = menus.value.findIndex((m) => m.path === route.path)
  return idx < 0 ? 0 : idx
})

const today = computed(() =>
  new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })
)

const transitionName = ref('fwd')
watch(activeIndex, (next, prev) => {
  transitionName.value = next >= prev ? 'fwd' : 'back'
})

const showTop = ref(false)
let ticking = false

function onScroll() {
  if (ticking) return
  ticking = true
  requestAnimationFrame(() => {
    showTop.value = window.scrollY > 110
    ticking = false
  })
}

function scrollToTop() {
  const behavior = motionTier.value === 'reduced' ? 'auto' : 'smooth'
  window.scrollTo({ top: 0, behavior })
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

async function onCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
    return
  }
  if (command === 'logout') {
    await ElMessageBox.confirm('确定退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await auth.logout()
    router.replace('/login')
  }
}
</script>

<style scoped>
.route-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2.5px;
  z-index: 9999;
  opacity: 0;
  transition: opacity 0.3s var(--ease);
  pointer-events: none;
}

.route-progress.active {
  opacity: 1;
}

.route-progress span {
  display: block;
  height: 100%;
  width: 100%;
  transform: scaleX(0);
  transform-origin: 0 50%;
  background: linear-gradient(90deg, #0a84ff, #5e5ce6 55%, #af52de);
  box-shadow: 0 0 12px rgba(10, 132, 255, 0.55);
}

.route-progress.active span {
  animation: progress-run 1.1s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
}

@keyframes progress-run {
  0% {
    transform: scaleX(0);
  }
  55% {
    transform: scaleX(0.72);
  }
  100% {
    transform: scaleX(0.94);
  }
}

.motion-dot {
  position: absolute;
  right: 7px;
  bottom: 7px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--ios-blue);
  box-shadow: 0 0 0 2px #f2f2f7;
  transition: background 0.25s var(--ease);
}

.motion-dot.off {
  background: var(--label-4);
}

.back-top {
  position: fixed;
  right: 26px;
  bottom: 26px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(18px) saturate(180%);
  -webkit-backdrop-filter: blur(18px) saturate(180%);
  color: var(--label-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 60;
  box-shadow: 0 6px 20px rgba(31, 45, 61, 0.14);
  transition: transform 0.25s var(--spring), background 0.2s;
}

.back-top:hover {
  transform: translateY(-3px);
  background: #fff;
}

.back-top:active {
  transform: scale(0.92);
}

.fab-enter-active {
  transition: opacity 0.28s var(--ease), transform 0.42s var(--spring);
}

.fab-leave-active {
  transition: opacity 0.18s var(--ease), transform 0.2s var(--ease);
}

.fab-enter-from,
.fab-leave-to {
  opacity: 0;
  transform: translateY(14px) scale(0.8);
}

.shell {
  min-height: 100vh;
  display: flex;
  gap: 18px;
  padding: 16px;
  background:
    radial-gradient(1200px 600px at 12% -10%, rgba(0, 122, 255, 0.08), transparent 60%),
    radial-gradient(900px 500px at 100% 0%, rgba(175, 82, 222, 0.07), transparent 55%),
    #f2f2f7;
}

.sidebar {
  width: 236px;
  flex-shrink: 0;
  position: sticky;
  top: 16px;
  height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  padding: 20px 14px 16px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.02), 0 18px 40px rgba(31, 45, 61, 0.08);
  animation: rise 0.6s var(--ease-out) both;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 4px 8px 22px;
}

.app-icon {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(145deg, #33a1ff 0%, #007aff 55%, #5856d6 100%);
  box-shadow: 0 8px 18px rgba(0, 122, 255, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.brand-text strong {
  font-size: 15px;
  letter-spacing: -0.01em;
}

.brand-text span {
  font-size: 10.5px;
  color: var(--label-3);
  letter-spacing: 0.04em;
}

.nav {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 2px;
}

.nav-pill {
  position: absolute;
  left: 2px;
  right: 2px;
  top: 0;
  height: 46px;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.06), 0 8px 20px rgba(16, 24, 40, 0.08);
  transform: translateY(calc(var(--idx, 0) * 52px));
  transition: transform 0.5s var(--spring);
  z-index: 0;
}

.nav-item {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 11px;
  height: 46px;
  padding: 0 14px;
  border: none;
  border-radius: 14px;
  background: transparent;
  color: var(--label-2);
  font-size: 14px;
  font-family: inherit;
  font-weight: 500;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: color 0.2s var(--ease), transform 0.2s var(--spring);
}

.nav-item:hover {
  color: var(--label);
}

.nav-item:active {
  transform: scale(0.97);
}

.nav-item.active {
  color: var(--label);
  font-weight: 600;
}

.nav-item.active .el-icon {
  color: var(--ios-blue);
}

.side-foot {
  margin-top: auto;
  padding: 10px 6px 2px;
}

.side-note {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(120, 120, 128, 0.07);
}

.side-note .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ios-green);
  box-shadow: 0 0 0 4px rgba(52, 199, 89, 0.15);
  animation: pulse-soft 2.4s ease-in-out infinite;
}

.side-note div {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.side-note strong {
  font-size: 11.5px;
  color: var(--label);
}

.side-note span {
  font-size: 10.5px;
  color: var(--label-3);
}

.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 58px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 6px 0 10px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.today {
  font-size: 12.5px;
  color: var(--label-3);
  letter-spacing: 0;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 26px;
  padding: 0 11px;
  border-radius: 999px;
  background: rgba(52, 199, 89, 0.11);
  color: #248a3d;
  font-size: 11.5px;
  font-weight: 500;
}

.status-chip i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ios-green);
  box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.16);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: var(--label-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s var(--ease), transform 0.2s var(--spring);
}

.icon-btn:hover {
  background: rgba(120, 120, 128, 0.1);
}

.icon-btn:active {
  transform: scale(0.92);
}

.icon-btn .badge {
  position: absolute;
  top: 8px;
  right: 9px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ios-red);
  border: 1.5px solid #f2f2f7;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 5px 8px 5px 5px;
  border-radius: 999px;
  cursor: pointer;
  transition: background 0.2s var(--ease);
}

.user-chip:hover {
  background: rgba(120, 120, 128, 0.08);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(145deg, #5ac8fa, #007aff 70%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.user-meta strong {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--label);
}

.user-meta span {
  font-size: 10.5px;
  color: var(--label-3);
}

.chevron {
  color: var(--label-3);
}

.content {
  flex: 1;
  min-width: 0;
  padding: 4px 10px 10px;
}

@media (max-width: 980px) {
  .shell {
    padding: 10px;
    gap: 12px;
  }
  .sidebar {
    width: 78px;
    padding: 16px 10px;
  }
  .brand-text,
  .nav-item span,
  .side-note div,
  .nav-badge {
    display: none;
  }
  .brand {
    justify-content: center;
    padding: 4px 0 18px;
  }
  .nav-item {
    justify-content: center;
    padding: 0;
  }
  .side-note {
    justify-content: center;
    padding: 12px 0;
  }
  .user-meta,
  .today {
    display: none;
  }
  .content {
    padding: 4px 2px;
  }
}
</style>
