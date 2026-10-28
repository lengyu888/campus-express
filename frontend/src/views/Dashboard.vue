<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>{{ greeting }}，{{ auth.user?.name }}</h1>
        <p>{{ today }} · {{ auth.user?.student_no || auth.roleLabel }}</p>
      </div>
      <el-button round :icon="Refresh" :loading="loading" @click="refresh">刷新状态</el-button>
    </header>

    <section class="hero" ref="heroRef" v-reveal @pointermove="onHeroMove" @pointerleave="resetHero">
      <div class="hero-glow"></div>
      <div class="hero-content">
        <span class="hero-eyebrow">阶段五 · 测试与验收</span>
        <h2>系统已全部上线</h2>
        <p>认证、驿站、收件、寄件、异常、通知与统计全部完成，184 项接口自测全部通过，已进入部署验收阶段。</p>
        <div class="hero-chips">
          <span class="chip" :class="health.database === 'up' ? 'ok' : 'bad'">
            <i></i> MySQL {{ health.database === 'up' ? '已连接' : '未连接' }}
          </span>
          <span class="chip" :class="health.redis === 'up' ? 'ok' : 'warn'">
            <i></i> Redis {{ health.redis === 'up' ? '已连接' : '降级运行' }}
          </span>
        </div>
      </div>
      <div class="hero-orbit">
        <div class="ring r1"></div>
        <div class="ring r2"></div>
        <div class="ring r3"></div>
        <div class="core">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 8.5 12 3 3 8.5v7L12 21l9-5.5z" />
            <path d="M3 8.5 12 14l9-5.5M12 14v7" />
          </svg>
        </div>
      </div>
    </section>

    <section class="stats">
      <article
        v-for="(item, i) in stats"
        :key="item.label"
        class="stat card"
        v-reveal="120 + i * 70"
        @pointermove="onStatMove"
        @pointerleave="resetStat"
      >
        <div class="stat-icon" :style="{ background: item.tint, color: item.color }">
          <el-icon :size="19"><component :is="item.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-label">{{ item.label }}</span>
          <strong class="stat-value">{{ display[i] }}</strong>
          <span class="stat-hint">{{ item.hint }}</span>
        </div>
      </article>
    </section>

    <section class="soon">
      <article
        v-for="(item, i) in quickCards"
        :key="item.title"
        class="soon-card card"
        :class="{ clickable: item.path }"
        v-reveal="120 + i * 70"
        @click="item.path && router.push(item.path)"
      >
        <div class="stat-icon" :style="{ background: item.tint, color: item.color }">
          <el-icon :size="19"><component :is="item.icon" /></el-icon>
        </div>
        <div>
          <strong>{{ item.title }}</strong>
          <p>{{ item.desc }}</p>
        </div>
        <span class="soon-tag" :class="{ live: item.path }">{{ item.stage }}</span>
      </article>
    </section>

    <section class="grid">
      <div class="panel card" v-reveal="320">
        <div class="panel-head">
          <div>
            <h3>开发进度</h3>
            <p>按阶段验收，确认后提交</p>
          </div>
          <span class="panel-meta">5 / 5</span>
        </div>
        <div class="timeline">
          <div v-for="stage in stages" :key="stage.name" class="stage" :class="stage.state">
            <div class="stage-dot"></div>
            <div class="stage-body">
              <div class="stage-title">
                <strong>{{ stage.name }}</strong>
                <span class="stage-pill">{{ stage.stateText }}</span>
              </div>
              <p>{{ stage.desc }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="panel card" v-reveal="400">
        <div class="panel-head">
          <div>
            <h3>验收指引</h3>
            <p>建议按顺序体验</p>
          </div>
        </div>
        <ol class="checklist">
          <li v-for="(item, i) in checks" :key="i">
            <span class="num">{{ i + 1 }}</span>
            <span>{{ item }}</span>
          </li>
        </ol>
        <div class="note">
          <el-icon :size="15"><InfoFilled /></el-icon>
          <span>演示账号见登录页，可在个人中心修改密码</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import {
  Refresh, Box, Warning, Clock, CircleCheck, Van, Bell, InfoFilled, DataLine, Tickets
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { listPackages, packagesSummary } from '../api/packages'
import { motionTier } from '../motion'

const auth = useAuthStore()
const router = useRouter()
const heroRef = ref(null)
const loading = ref(false)
let scrollTicking = false
const health = reactive({ database: 'down', redis: 'down' })

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const today = computed(() =>
  new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })
)

const staffStats = [
  { label: '在库包裹', value: 0, hint: '待取件', icon: Box, tint: 'rgba(0,122,255,.12)', color: '#007aff' },
  { label: '超期', value: 0, hint: '超过 3 天', icon: Warning, tint: 'rgba(255,149,0,.14)', color: '#c26a00' },
  { label: '今日入库', value: 0, hint: '登记件数', icon: Clock, tint: 'rgba(52,199,89,.13)', color: '#248a3d' },
  { label: '今日出库', value: 0, hint: '核验取件', icon: CircleCheck, tint: 'rgba(175,82,222,.12)', color: '#8944ab' }
]

const studentStats = [
  { label: '待取件', value: 0, hint: '凭取件码领取', icon: Tickets, tint: 'rgba(0,122,255,.12)', color: '#007aff' },
  { label: '超期', value: 0, hint: '超过 3 天', icon: Warning, tint: 'rgba(255,149,0,.14)', color: '#c26a00' },
  { label: '已取件', value: 0, hint: '历史完成', icon: CircleCheck, tint: 'rgba(52,199,89,.13)', color: '#248a3d' },
  { label: '累计包裹', value: 0, hint: '全部记录', icon: Box, tint: 'rgba(175,82,222,.12)', color: '#8944ab' }
]

const stats = ref(staffStats)

const display = ref([0, 0, 0, 0])
let rafId = 0

function animateNumbers(targets) {
  cancelAnimationFrame(rafId)
  const start = performance.now()
  const duration = 900
  const from = display.value.slice()
  const step = (now) => {
    const t = Math.min((now - start) / duration, 1)
    const eased = 1 - Math.pow(1 - t, 3)
    display.value = from.map((v, i) => Math.round(v + (targets[i] - v) * eased))
    if (t < 1) rafId = requestAnimationFrame(step)
  }
  rafId = requestAnimationFrame(step)
}

const studentSoon = [
  { title: '我的寄件', desc: '在线下单、运费估算与轨迹', stage: '可用', icon: Van, tint: 'rgba(255,149,0,.14)', color: '#c26a00', path: '/shipments' },
  { title: '消息中心', desc: '取件提醒、寄件进展与公告', stage: '可用', icon: Bell, tint: 'rgba(52,199,89,.13)', color: '#248a3d', path: '/notifications' },
  { title: '我的包裹', desc: '取件码、超期提醒与状态跟踪', stage: '可用', icon: Tickets, tint: 'rgba(0,122,255,.12)', color: '#007aff', path: '/my-packages' }
]

const staffSoon = [
  { title: '异常处理', desc: '破损、丢失与错分件的跟进', stage: '可用', icon: Warning, tint: 'rgba(255,59,48,.1)', color: '#b3261e', path: '/exceptions' },
  { title: '统计报表', desc: '收发量、超期率与驿站工作量', stage: '可用', icon: DataLine, tint: 'rgba(175,82,222,.12)', color: '#8944ab', path: '/stats' },
  { title: '消息中心', desc: '取件提醒、寄件进展与公告', stage: '可用', icon: Bell, tint: 'rgba(52,199,89,.13)', color: '#248a3d', path: '/notifications' }
]

const quickCards = computed(() => (auth.role === 'student' ? studentSoon : staffSoon))

const stages = [
  { name: '阶段一 认证与用户管理', state: 'done', stateText: '已完成', desc: 'Docker 基础设施、JWT 登录、账号与角色管理' },
  { name: '阶段二 驿站与货架管理', state: 'done', stateText: '已完成', desc: '驿站档案、货架分区、容量与占用率' },
  { name: '阶段三 快递入库与取件出库', state: 'done', stateText: '已完成', desc: '运单登记、格口分配、取件码、双重核验出库' },
  { name: '阶段四 寄件、通知与统计', state: 'done', stateText: '已完成', desc: '寄件下单、轨迹跟踪、消息通知与报表' },
  { name: '阶段五 异常、日志与测试验收', state: 'done', stateText: '待验收', desc: '异常处理、操作日志、测试用例与部署验收' }
]

const checks = [
  '工作人员进入「异常处理」，将待处理异常转为处理中',
  '解决异常并选择「重新入库」，确认包裹恢复在库',
  '管理员进入「操作日志」，按模块筛选查看写操作',
  '学生下单寄件，工作人员完成揽收、发出与签收',
  '在「统计报表」确认超期率与趋势数据同步更新'
]

async function loadHealth() {
  try {
    const { data } = await axios.get('/api/v1/health')
    health.database = data.data.database
    health.redis = data.data.redis
  } catch (e) {
    health.database = 'down'
    health.redis = 'down'
  }
}

async function loadStats() {
  let values = [0, 0, 0, 0]

  if (auth.role === 'student') {
    stats.value = studentStats
    const data = await listPackages({ page: 1, page_size: 100 })
    const items = data.items || []
    values = [
      items.filter((p) => p.status === 'in_stock').length,
      items.filter((p) => p.status === 'overdue').length,
      items.filter((p) => p.status === 'picked').length,
      data.total
    ]
  } else {
    stats.value = staffStats
    const data = await packagesSummary()
    values = [data.in_stock, data.overdue, data.today_inbound, data.today_picked]
  }

  stats.value = stats.value.map((s, i) => ({ ...s, value: values[i] }))
  animateNumbers(values)
}

async function refresh() {
  loading.value = true
  try {
    await Promise.all([loadHealth(), loadStats()])
  } finally {
    loading.value = false
  }
}

function onHeroMove(event) {
  if (motionTier.value !== 'full' || !heroRef.value) return
  const rect = heroRef.value.getBoundingClientRect()
  const x = (event.clientX - rect.left) / rect.width - 0.5
  const y = (event.clientY - rect.top) / rect.height - 0.5
  heroRef.value.style.setProperty('--hx', x.toFixed(3))
  heroRef.value.style.setProperty('--hy', y.toFixed(3))
}

function resetHero() {
  if (!heroRef.value) return
  heroRef.value.style.setProperty('--hx', '0')
  heroRef.value.style.setProperty('--hy', '0')
}

function onStatMove(event) {
  if (motionTier.value !== 'full') return
  const el = event.currentTarget
  const rect = el.getBoundingClientRect()
  const px = event.clientX - rect.left
  const py = event.clientY - rect.top
  el.style.setProperty('--mx', `${px}px`)
  el.style.setProperty('--my', `${py}px`)
  const rx = ((py / rect.height) - 0.5) * -5
  const ry = ((px / rect.width) - 0.5) * 5
  el.style.transform = `perspective(900px) rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) translateY(-4px)`
}

function resetStat(event) {
  event.currentTarget.style.transform = ''
}

function onScroll() {
  if (motionTier.value !== 'full' || scrollTicking) return
  scrollTicking = true
  requestAnimationFrame(() => {
    if (heroRef.value) {
      heroRef.value.style.setProperty('--sy', String(Math.min(window.scrollY, 420)))
    }
    scrollTicking = false
  })
}

onMounted(() => {
  refresh()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  --hx: 0;
  --hy: 0;
  --sy: 0;
  display: flex;
  justify-content: space-between;
  gap: 30px;
  padding: 30px 32px;
  border-radius: 26px;
  color: #fff;
  background: linear-gradient(130deg, #0a84ff 0%, #5e5ce6 58%, #af52de 100%);
  box-shadow: 0 18px 40px rgba(94, 92, 230, 0.28);
  margin-bottom: 16px;
  isolation: isolate;
  transition: box-shadow 0.4s var(--ease);
}

.hero:hover {
  box-shadow: 0 22px 50px rgba(94, 92, 230, 0.34);
}

.hero-glow {
  position: absolute;
  width: 460px;
  height: 460px;
  right: -100px;
  top: -200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.35), transparent 65%);
  z-index: -1;
  transform: translate3d(
    calc(var(--hx, 0) * -26px),
    calc(var(--hy, 0) * -20px + var(--sy, 0) * 0.12px),
    0
  );
  transition: transform 0.5s var(--ease-out);
}

.hero-content {
  max-width: 560px;
  position: relative;
  z-index: 1;
}

.hero-eyebrow {
  display: inline-block;
  font-size: 11.5px;
  letter-spacing: 0.04em;
  padding: 4px 11px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.22);
  margin-bottom: 14px;
}

.hero h2 {
  margin: 0 0 9px;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.hero p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.82);
}

.hero-chips {
  display: flex;
  gap: 8px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 27px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 11.5px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
}

.chip i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a7f3c0;
}

.chip.warn i {
  background: #ffd60a;
}

.chip.bad i {
  background: #ff6961;
}

.hero-orbit {
  position: relative;
  width: 170px;
  height: 170px;
  flex-shrink: 0;
  align-self: center;
  transform: translate3d(calc(var(--hx, 0) * 18px), calc(var(--hy, 0) * 14px), 0);
  transition: transform 0.45s var(--ease-out);
}

.ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.25);
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.r1 {
  width: 170px;
  height: 170px;
  animation: spin 26s linear infinite;
  border-style: dashed;
}

.r2 {
  width: 122px;
  height: 122px;
  border-color: rgba(255, 255, 255, 0.3);
}

.r3 {
  width: 78px;
  height: 78px;
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.35);
}

.core {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 54px;
  height: 54px;
  transform: translate(-50%, -50%);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(14px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.12);
}

@keyframes spin {
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.stat {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 18px;
  transform-style: preserve-3d;
  transition: transform 0.3s var(--ease-out), box-shadow 0.35s var(--ease);
  will-change: transform;
}

.stat > * {
  position: relative;
  z-index: 1;
}

.stat::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(
    240px circle at var(--mx, 50%) var(--my, 50%),
    rgba(0, 122, 255, 0.12),
    transparent 62%
  );
  opacity: 0;
  transition: opacity 0.3s var(--ease);
  pointer-events: none;
}

.stat:hover {
  box-shadow: var(--shadow-md);
}

.stat:hover::after {
  opacity: 1;
}

.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-body {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  min-width: 0;
}

.stat-label {
  font-size: 11.5px;
  color: var(--label-3);
}

.stat-value {
  font-size: 27px;
  font-weight: 700;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  color: var(--label);
  margin: 2px 0 1px;
}

.stat-hint {
  font-size: 10.5px;
  color: var(--label-4);
}

.soon {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.soon-card {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 18px;
  position: relative;
}

.soon-card strong {
  font-size: 13.5px;
}

.soon-card p {
  margin: 3px 0 0;
  font-size: 11.5px;
  color: var(--label-3);
  line-height: 1.5;
}

.soon-tag {
  position: absolute;
  top: 14px;
  right: 14px;
  font-size: 10px;
  color: var(--label-3);
  background: var(--fill-2);
  padding: 2px 8px;
  border-radius: 999px;
}

.soon-tag.live {
  color: #1d7a37;
  background: rgba(52, 199, 89, 0.14);
  font-weight: 600;
}

.soon-card.clickable {
  cursor: pointer;
  transition: transform 0.3s var(--spring), box-shadow 0.3s var(--ease);
}

.soon-card.clickable:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.soon-card.clickable:active {
  transform: scale(0.985);
}

.grid {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 14px;
}

.panel {
  padding: 24px 26px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.panel-head h3 {
  margin: 0 0 3px;
  font-size: 15.5px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.panel-head p {
  margin: 0;
  font-size: 11.5px;
  color: var(--label-3);
}

.panel-meta {
  font-size: 11px;
  color: var(--label-3);
  font-variant-numeric: tabular-nums;
  background: var(--fill-2);
  padding: 4px 9px;
  border-radius: 999px;
}

.timeline {
  display: flex;
  flex-direction: column;
}

.stage {
  position: relative;
  display: flex;
  gap: 13px;
  padding-bottom: 19px;
}

.stage:last-child {
  padding-bottom: 0;
}

.stage::before {
  content: "";
  position: absolute;
  left: 4px;
  top: 13px;
  bottom: 0;
  width: 1px;
  background: var(--separator);
}

.stage:last-child::before {
  display: none;
}

.stage-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-top: 5px;
  background: #d1d1d6;
  flex-shrink: 0;
  z-index: 1;
}

.stage.done .stage-dot {
  background: var(--ios-blue);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.13);
}

.stage-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-title strong {
  font-size: 12.8px;
  font-weight: 600;
  color: var(--label);
}

.stage-pill {
  font-size: 10px;
  color: var(--label-3);
  background: var(--fill-2);
  padding: 2px 8px;
  border-radius: 999px;
}

.stage.done .stage-pill {
  color: var(--ios-blue);
  background: rgba(0, 122, 255, 0.1);
}

.stage-body p {
  margin: 4px 0 0;
  font-size: 11.5px;
  color: var(--label-3);
  line-height: 1.55;
}

.checklist {
  list-style: none;
  margin: 0 0 18px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checklist li {
  display: flex;
  gap: 11px;
  font-size: 12.8px;
  color: var(--label-2);
  line-height: 1.5;
}

.num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--ios-blue);
  background: rgba(0, 122, 255, 0.1);
}

.note {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(0, 122, 255, 0.07);
  color: #0a5bb5;
  font-size: 11.5px;
}

@media (max-width: 1100px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .grid {
    grid-template-columns: 1fr;
  }
  .soon {
    grid-template-columns: 1fr;
  }
  .hero-orbit {
    display: none;
  }
}
</style>
