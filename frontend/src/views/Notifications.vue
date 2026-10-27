<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>消息中心</h1>
        <p>{{ unread }} 条未读通知 · {{ announcements.length }} 条公告</p>
      </div>
      <div class="head-actions">
        <el-button v-if="tab === 'notice'" round :icon="Check" :disabled="!unread" @click="readAll">
          全部已读
        </el-button>
        <el-button round :icon="Refresh" :loading="loading" @click="reload">刷新</el-button>
      </div>
    </header>

    <section class="toolbar card" v-reveal>
      <div class="seg" role="group" aria-label="消息分类">
        <button type="button" :class="{ active: tab === 'notice' }" @click="tab = 'notice'">
          通知
          <span v-if="unread" class="seg-badge">{{ unread }}</span>
        </button>
        <button type="button" :class="{ active: tab === 'announce' }" @click="tab = 'announce'">
          公告
          <span class="seg-count">{{ announcements.length }}</span>
        </button>
      </div>

      <div v-if="tab === 'notice'" class="chips">
        <button
          v-for="item in filters"
          :key="item.value"
          type="button"
          class="chip"
          :class="{ active: type === item.value }"
          @click="switchType(item.value)"
        >
          {{ item.label }}
        </button>
      </div>
    </section>

    <section v-if="tab === 'notice'" class="notice-card card" v-reveal="80">
      <div v-if="loading && !notices.length" class="skeleton">
        <div v-for="i in 4" :key="i" class="sk-row" :style="{ '--i': i }">
          <span class="sk-avatar"></span>
          <span class="sk-main"></span>
          <span class="sk-sub"></span>
        </div>
      </div>

      <div v-else-if="!notices.length" class="empty">
        <div class="empty-icon"><el-icon :size="24"><Bell /></el-icon></div>
        <h3>暂无通知</h3>
        <p>包裹到站、超期提醒与寄件进展都会在这里出现。</p>
      </div>

      <ul v-else class="notice-list">
        <li
          v-for="(item, i) in notices"
          :key="item.id"
          class="notice"
          :class="{ unread: !item.is_read }"
          :style="{ '--i': i }"
          @click="readOne(item)"
        >
          <span class="notice-icon" :class="`t-${item.type}`">
            <el-icon :size="17"><component :is="iconOf(item.type)" /></el-icon>
          </span>
          <div class="notice-body">
            <div class="notice-title">
              <strong>{{ item.title }}</strong>
              <span class="notice-type">{{ item.type_label }}</span>
            </div>
            <p>{{ item.content }}</p>
            <span class="notice-time mono">{{ fmt(item.created_at) }}</span>
          </div>
          <span v-if="!item.is_read" class="unread-dot" aria-label="未读"></span>
        </li>
      </ul>
    </section>

    <section v-else class="announce-list">
      <article
        v-for="(item, i) in announcements"
        :key="item.id"
        class="announce card"
        v-reveal="i * 60"
      >
        <div class="announce-head">
          <span class="announce-mark">
            <el-icon :size="16"><Document /></el-icon>
          </span>
          <div>
            <h3>{{ item.title }}</h3>
            <span class="announce-meta">
              {{ item.publisher_name || '系统' }} · {{ fmt(item.publish_at || item.created_at) }}
            </span>
          </div>
        </div>
        <p class="announce-content">{{ item.content }}</p>
      </article>

      <div v-if="!announcements.length" class="empty card">
        <div class="empty-icon"><el-icon :size="24"><Document /></el-icon></div>
        <h3>暂无公告</h3>
        <p>驿站运营公告会在这里发布。</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Bell, Refresh, Check, Box, Warning, Van, Document, InfoFilled
} from '@element-plus/icons-vue'
import {
  listAnnouncements, listNotifications, markAllRead, markRead, unreadCount
} from '../api/notifications'

const tab = ref('notice')
const notices = ref([])
const announcements = ref([])
const unread = ref(0)
const loading = ref(false)
const type = ref('')

const filters = [
  { label: '全部', value: '' },
  { label: '取件', value: 'pickup' },
  { label: '超期', value: 'overdue' },
  { label: '寄件', value: 'shipment' },
  { label: '系统', value: 'system' }
]

function iconOf(value) {
  return { pickup: Box, overdue: Warning, shipment: Van, system: InfoFilled }[value] || Bell
}

function fmt(value) {
  if (!value) return ''
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function loadNotices() {
  loading.value = true
  try {
    const data = await listNotifications({ page: 1, page_size: 50, type: type.value || undefined })
    notices.value = data.items
    unread.value = data.unread
  } finally {
    loading.value = false
  }
}

async function loadAnnouncements() {
  loading.value = true
  try {
    const data = await listAnnouncements({ page: 1, page_size: 20 })
    announcements.value = data.items
  } finally {
    loading.value = false
  }
}

async function reload() {
  if (tab.value === 'notice') await loadNotices()
  else await loadAnnouncements()
}

function switchType(value) {
  type.value = value
  loadNotices()
}

async function readOne(item) {
  if (item.is_read) return
  item.is_read = 1
  unread.value = Math.max(0, unread.value - 1)
  try {
    await markRead(item.id)
  } catch (e) {
    item.is_read = 0
    unread.value += 1
  }
}

async function readAll() {
  await markAllRead()
  notices.value = notices.value.map((n) => ({ ...n, is_read: 1 }))
  unread.value = 0
  ElMessage.success('已全部标记为已读')
  const data = await unreadCount()
  unread.value = data.unread
}

onMounted(async () => {
  await Promise.all([loadNotices(), loadAnnouncements()])
})
</script>

<style scoped>
.head-actions {
  display: flex;
  gap: 8px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.seg {
  display: inline-flex;
  padding: 3px;
  gap: 2px;
  border-radius: 12px;
  background: rgba(120, 120, 128, 0.12);
}

.seg button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  border-radius: 9px;
  padding: 7px 18px;
  font-family: inherit;
  font-size: 12.5px;
  color: var(--label-2);
  cursor: pointer;
  transition: all 0.3s var(--ease);
}

.seg button.active {
  background: #fff;
  color: var(--label);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.seg-badge {
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--ios-red);
  color: #fff;
  font-size: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.seg-count {
  font-size: 10.5px;
  color: var(--label-4);
}

.chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip {
  border: none;
  background: var(--fill-2);
  color: var(--label-2);
  font-family: inherit;
  font-size: 11.5px;
  padding: 5px 11px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.25s var(--ease);
}

.chip.active {
  background: rgba(0, 122, 255, 0.1);
  color: #0a5bb5;
  font-weight: 600;
}

.notice-card {
  padding: 6px 10px;
}

.notice-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.notice {
  position: relative;
  display: flex;
  gap: 13px;
  padding: 16px 12px;
  border-bottom: 1px solid var(--separator);
  cursor: pointer;
  border-radius: 12px;
  transition: background 0.2s var(--ease);
  animation: row-in 0.45s var(--ease-out) both;
  animation-delay: calc(var(--i) * 40ms);
}

.notice:last-child {
  border-bottom: none;
}

.notice:hover {
  background: rgba(0, 122, 255, 0.04);
}

@keyframes row-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
}

.notice-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.t-pickup {
  background: rgba(0, 122, 255, 0.1);
  color: #007aff;
}

.t-overdue {
  background: rgba(255, 149, 0, 0.14);
  color: #c26a00;
}

.t-shipment {
  background: rgba(52, 199, 89, 0.13);
  color: #248a3d;
}

.t-system {
  background: rgba(120, 120, 128, 0.12);
  color: var(--label-2);
}

.notice-body {
  flex: 1;
  min-width: 0;
}

.notice-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notice-title strong {
  font-size: 13px;
  font-weight: 600;
}

.notice-type {
  font-size: 10px;
  color: var(--label-3);
  background: var(--fill-2);
  padding: 1px 7px;
  border-radius: 999px;
}

.notice-body p {
  margin: 4px 0 5px;
  font-size: 12px;
  color: var(--label-2);
  line-height: 1.6;
}

.notice-time {
  font-size: 10.5px;
  color: var(--label-4);
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ios-blue);
  margin-top: 6px;
  flex-shrink: 0;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}

.notice.unread .notice-title strong {
  color: var(--label);
}

.notice:not(.unread) .notice-title strong {
  color: var(--label-2);
  font-weight: 550;
}

.announce-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.announce {
  padding: 22px 24px;
}

.announce-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 10px;
}

.announce-mark {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  background: rgba(0, 122, 255, 0.09);
  color: var(--ios-blue);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.announce h3 {
  margin: 0 0 3px;
  font-size: 14.5px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.announce-meta {
  font-size: 11px;
  color: var(--label-3);
}

.announce-content {
  margin: 0;
  font-size: 12.5px;
  color: var(--label-2);
  line-height: 1.75;
  white-space: pre-wrap;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 56px 20px;
  text-align: center;
}

.empty-icon {
  width: 54px;
  height: 54px;
  border-radius: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 122, 255, 0.08);
  color: var(--ios-blue);
  margin-bottom: 6px;
}

.empty h3 {
  margin: 0;
  font-size: 14px;
}

.empty p {
  margin: 0;
  font-size: 12px;
  color: var(--label-3);
}

.mono {
  font-family: 'SF Mono', Consolas, monospace;
}

.skeleton {
  padding: 12px;
}

.sk-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 6px;
  border-bottom: 1px solid var(--separator);
  opacity: 0;
  animation: fade-in 0.35s var(--ease-out) forwards;
  animation-delay: calc(var(--i) * 40ms);
}

.sk-avatar,
.sk-main,
.sk-sub {
  background: linear-gradient(90deg, rgba(120, 120, 128, 0.1) 25%, rgba(120, 120, 128, 0.16) 37%, rgba(120, 120, 128, 0.1) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
  border-radius: 8px;
}

.sk-avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
}

.sk-main {
  width: 160px;
  height: 12px;
}

.sk-sub {
  width: 220px;
  height: 10px;
}

@keyframes shimmer {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

@keyframes fade-in {
  to { opacity: 1; }
}
</style>
