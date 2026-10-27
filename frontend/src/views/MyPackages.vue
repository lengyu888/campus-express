<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>我的包裹</h1>
        <p>{{ rows.length }} 件包裹 · {{ counts.in_stock }} 件待取 · {{ counts.overdue }} 件超期</p>
      </div>
      <div class="head-actions">
        <el-button round :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <section class="stats">
      <article class="stat card" v-reveal>
        <div class="stat-icon blue"><el-icon :size="18"><Box /></el-icon></div>
        <div class="stat-body">
          <span class="stat-label">待取件</span>
          <strong class="stat-value tabular">{{ counts.in_stock }}</strong>
          <span class="stat-hint">凭取件码到驿站取件</span>
        </div>
      </article>
      <article class="stat card" v-reveal="60">
        <div class="stat-icon orange"><el-icon :size="18"><Warning /></el-icon></div>
        <div class="stat-body">
          <span class="stat-label">超期</span>
          <strong class="stat-value tabular">{{ counts.overdue }}</strong>
          <span class="stat-hint">超过 3 天未取</span>
        </div>
      </article>
      <article class="stat card" v-reveal="120">
        <div class="stat-icon green"><el-icon :size="18"><CircleCheck /></el-icon></div>
        <div class="stat-body">
          <span class="stat-label">已取件</span>
          <strong class="stat-value tabular">{{ counts.picked }}</strong>
          <span class="stat-hint">历史完成</span>
        </div>
      </article>
    </section>

    <section class="toolbar card" v-reveal="80">
      <div class="seg" role="group" aria-label="包裹筛选">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          :class="{ active: filter === tab.value }"
          @click="filter = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
      <span class="toolbar-note">取件码有效期 7 天，请及时领取</span>
    </section>

    <section v-if="loading && !rows.length" class="grid">
      <div v-for="i in 4" :key="i" class="card sk-card">
        <div class="sk-line w40"></div>
        <div class="sk-line w70"></div>
        <div class="sk-block"></div>
      </div>
    </section>

    <section v-else-if="!visible.length" class="empty card" v-reveal>
      <div class="empty-icon"><el-icon :size="26"><Box /></el-icon></div>
      <h3>{{ rows.length ? '该分类下暂无包裹' : '还没有包裹' }}</h3>
      <p>{{ rows.length ? '切换上方分类看看。' : '快递到站后会在这里显示取件码。' }}</p>
    </section>

    <section v-else class="grid">
      <article
        v-for="(item, i) in visible"
        :key="item.id"
        class="pkg card"
        :class="`is-${item.status}`"
        v-reveal="i * 60"
        @click="openDetail(item)"
      >
        <div class="pkg-head">
          <span class="courier">{{ item.courier_company }}</span>
          <span class="pill" :class="`st-${item.status}`">{{ item.status_label }}</span>
        </div>

        <div v-if="item.pickup_code" class="code-block">
          <span class="code-label">取件码</span>
          <strong class="code tabular">{{ item.pickup_code }}</strong>
          <span class="code-expire">有效期至 {{ fmtDate(item.code_expire_at) }}</span>
        </div>

        <div v-else class="code-block muted-block">
          <span class="code-label">{{ item.status === 'picked' ? '已完成取件' : '取件码已失效' }}</span>
          <strong class="code-sub">{{ item.status === 'picked' ? fmt(item.picked_at) : item.status_label }}</strong>
        </div>

        <dl class="pkg-info">
          <div><dt>运单号</dt><dd class="mono">{{ item.tracking_no }}</dd></div>
          <div><dt>驿站</dt><dd>{{ item.station_name }}</dd></div>
          <div><dt>格口</dt><dd>{{ item.shelf_code || '—' }}</dd></div>
          <div><dt>入库</dt><dd>{{ fmtDate(item.stored_at) }}</dd></div>
        </dl>

        <div v-if="item.status === 'overdue'" class="warn">
          <el-icon :size="13"><Warning /></el-icon>
          已超期 {{ item.overdue_days }} 天，请尽快取件
        </div>

        <div class="pkg-foot">
          <span class="type">{{ typeLabel(item.package_type) }}</span>
          <button class="link" type="button" @click.stop="openDetail(item)">
            查看详情
            <el-icon :size="12"><ArrowRight /></el-icon>
          </button>
        </div>
      </article>
    </section>

    <el-drawer v-model="detailVisible" :with-header="false" size="440px">
      <div v-if="detail" class="detail">
        <div class="drawer-head">
          <div>
            <h3>{{ detail.tracking_no }}</h3>
            <span>{{ detail.courier_company }} · {{ typeLabel(detail.package_type) }}</span>
          </div>
          <button class="drawer-close" type="button" aria-label="关闭" @click="detailVisible = false">
            <el-icon :size="16"><Close /></el-icon>
          </button>
        </div>

        <div v-if="detail.pickup_code" class="detail-code">
          <span>取件码</span>
          <strong class="tabular">{{ detail.pickup_code }}</strong>
          <button type="button" aria-label="复制取件码" @click="copyCode(detail.pickup_code)">
            <el-icon :size="14"><CopyDocument /></el-icon>
          </button>
        </div>

        <div class="detail-status" :class="`st-${detail.status}`">
          <span class="pill" :class="`st-${detail.status}`">{{ detail.status_label }}</span>
          <span>{{ statusHeadline(detail) }}</span>
        </div>

        <dl class="detail-grid">
          <div><dt>驿站</dt><dd>{{ detail.station_name }}</dd></div>
          <div><dt>格口</dt><dd>{{ detail.shelf_code || '已释放' }}</dd></div>
          <div><dt>入库时间</dt><dd class="mono">{{ fmt(detail.stored_at) }}</dd></div>
          <div><dt>在库天数</dt><dd>{{ detail.days_in_stock }} 天</dd></div>
          <div><dt>收件人</dt><dd>{{ detail.recipient_name }}</dd></div>
          <div><dt>手机号</dt><dd class="tabular">{{ detail.recipient_phone }}</dd></div>
        </dl>

        <h4 class="timeline-title">物流节点</h4>
        <div class="timeline">
          <div v-for="(item, i) in detail.timeline" :key="i" class="tl-item" :class="item.type">
            <span class="tl-dot"></span>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.desc }}</p>
              <span class="tl-time mono">{{ fmt(item.at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, Box, Warning, CircleCheck, ArrowRight, Close, CopyDocument
} from '@element-plus/icons-vue'
import { getPackage, listPackages } from '../api/packages'

const rows = ref([])
const loading = ref(false)
const filter = ref('')

const detailVisible = ref(false)
const detail = ref(null)

const counts = reactive({ in_stock: 0, overdue: 0, picked: 0, total: 0 })

const tabs = [
  { label: '全部', value: '' },
  { label: '待取件', value: 'in_stock' },
  { label: '超期', value: 'overdue' },
  { label: '已取件', value: 'picked' }
]

const types = { normal: '普通件', fragile: '易碎品', large: '大件', doc: '文件' }

function typeLabel(value) {
  return types[value] || value
}

const visible = computed(() => {
  if (!filter.value) return rows.value
  return rows.value.filter((r) => r.status === filter.value)
})

function fmtDate(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function fmt(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function statusHeadline(row) {
  if (row.status === 'picked') return `已于 ${fmt(row.picked_at)} 完成取件`
  if (row.status === 'overdue') return `已超期 ${row.overdue_days} 天，请尽快到驿站取件`
  if (row.status === 'returned') return '包裹已退回发件方'
  if (row.status === 'exception') return '包裹异常，驿站会与您联系'
  return '包裹在库，凭取件码到驿站取件'
}

function copyCode(code) {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(String(code)).then(
      () => ElMessage.success(`取件码 ${code} 已复制`),
      () => ElMessage.warning(`取件码 ${code}`)
    )
  } else {
    ElMessage.success(`取件码 ${code}`)
  }
}

async function openDetail(row) {
  const data = await getPackage(row.id)
  detail.value = data
  detailVisible.value = true
}

async function load() {
  loading.value = true
  try {
    const data = await listPackages({ page: 1, page_size: 100 })
    rows.value = data.items
    counts.total = data.total
    counts.in_stock = data.items.filter((r) => r.status === 'in_stock').length
    counts.overdue = data.items.filter((r) => r.status === 'overdue').length
    counts.picked = data.items.filter((r) => r.status === 'picked').length
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.head-actions {
  display: flex;
  gap: 8px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 17px 18px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.blue {
  background: rgba(0, 122, 255, 0.12);
  color: #007aff;
}

.stat-icon.orange {
  background: rgba(255, 149, 0, 0.14);
  color: #c26a00;
}

.stat-icon.green {
  background: rgba(52, 199, 89, 0.13);
  color: #248a3d;
}

.stat-body {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.stat-label {
  font-size: 11.5px;
  color: var(--label-3);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 2px 0 1px;
}

.stat-hint {
  font-size: 10.5px;
  color: var(--label-4);
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

.toolbar-note {
  font-size: 11.5px;
  color: var(--label-3);
}

.seg {
  display: inline-flex;
  padding: 3px;
  gap: 2px;
  border-radius: 12px;
  background: rgba(120, 120, 128, 0.12);
}

.seg button {
  border: none;
  background: transparent;
  border-radius: 9px;
  padding: 7px 16px;
  font-family: inherit;
  font-size: 12.5px;
  color: var(--label-2);
  cursor: pointer;
  transition: all 0.3s var(--ease);
}

.seg button:active {
  transform: scale(0.96);
}

.seg button.active {
  background: #fff;
  color: var(--label);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.pkg {
  padding: 20px 22px 16px;
  cursor: pointer;
  transition: transform 0.32s var(--spring), box-shadow 0.3s var(--ease);
}

.pkg:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.pkg-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.courier {
  font-size: 12px;
  color: var(--label-2);
  font-weight: 550;
}

.code-block {
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.09), rgba(94, 92, 230, 0.1));
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 16px;
}

.code-label {
  font-size: 10.5px;
  color: var(--label-3);
}

.code {
  font-size: 34px;
  letter-spacing: 0.22em;
  font-weight: 700;
  color: #0a5bb5;
  line-height: 1.15;
}

.code-expire {
  font-size: 10.5px;
  color: var(--label-4);
}

.muted-block {
  background: var(--fill-2);
}

.code-sub {
  font-size: 15px;
  color: var(--label-2);
  font-weight: 600;
}

.pkg-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px 14px;
  margin: 0 0 12px;
}

.pkg-info dt {
  font-size: 10.5px;
  color: var(--label-3);
  margin-bottom: 1px;
}

.pkg-info dd {
  margin: 0;
  font-size: 12px;
  color: var(--label);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.warn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  color: #a85900;
  background: rgba(255, 149, 0, 0.12);
  border-radius: 10px;
  padding: 8px 10px;
  margin-bottom: 10px;
}

.pkg-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--separator);
}

.type {
  font-size: 11px;
  color: var(--label-4);
}

.link {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  border: none;
  background: transparent;
  color: var(--ios-blue);
  font-family: inherit;
  font-size: 12px;
  cursor: pointer;
  padding: 3px 4px;
  transition: gap 0.25s var(--ease);
}

.link:hover {
  gap: 7px;
}

.pill {
  display: inline-flex;
  align-items: center;
  height: 21px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
}

.st-in_stock {
  background: rgba(0, 122, 255, 0.1);
  color: #0a5bb5;
}

.st-overdue {
  background: rgba(255, 149, 0, 0.14);
  color: #a85900;
}

.st-picked {
  background: rgba(52, 199, 89, 0.13);
  color: #1d7a37;
}

.st-returned {
  background: rgba(120, 120, 128, 0.13);
  color: var(--label-2);
}

.st-exception {
  background: rgba(255, 59, 48, 0.12);
  color: #b3261e;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 122, 255, 0.08);
  color: var(--ios-blue);
  margin-bottom: 6px;
}

.empty h3 {
  margin: 0;
  font-size: 14.5px;
}

.empty p {
  margin: 0;
  font-size: 12px;
  color: var(--label-3);
}

.mono {
  font-family: 'SF Mono', 'JetBrains Mono', Consolas, monospace;
}

/* 骨架 */
.sk-card {
  padding: 22px;
}

.sk-line,
.sk-block {
  background: linear-gradient(90deg, rgba(120, 120, 128, 0.1) 25%, rgba(120, 120, 128, 0.16) 37%, rgba(120, 120, 128, 0.1) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
  border-radius: 8px;
}

.sk-line {
  height: 12px;
  margin-bottom: 10px;
}

.sk-block {
  height: 76px;
  border-radius: 16px;
}

.w40 { width: 40%; }
.w70 { width: 70%; }

@keyframes shimmer {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

/* 详情 */
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.drawer-head h3 {
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 700;
}

.drawer-head span {
  font-size: 12px;
  color: var(--label-3);
}

.drawer-close {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 9px;
  background: rgba(120, 120, 128, 0.1);
  color: var(--label-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.detail-code {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.09), rgba(94, 92, 230, 0.1));
  margin-bottom: 14px;
}

.detail-code span {
  font-size: 11.5px;
  color: var(--label-3);
}

.detail-code strong {
  font-size: 26px;
  letter-spacing: 0.2em;
  color: #0a5bb5;
}

.detail-code button {
  margin-left: auto;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  color: #0a5bb5;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-status {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 12px;
  color: var(--label-2);
  background: var(--fill-2);
  border-radius: 14px;
  padding: 12px 14px;
  margin-bottom: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  margin: 0 0 8px;
}

.detail-grid dt {
  font-size: 10.5px;
  color: var(--label-3);
  margin-bottom: 2px;
}

.detail-grid dd {
  margin: 0;
  font-size: 12.5px;
}

.timeline-title {
  margin: 22px 0 12px;
  font-size: 13px;
  font-weight: 650;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tl-item {
  position: relative;
  display: flex;
  gap: 12px;
}

.tl-item::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 14px;
  bottom: -16px;
  width: 1px;
  background: var(--separator);
}

.tl-item:last-child::before {
  display: none;
}

.tl-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--ios-blue);
  margin-top: 5px;
  flex-shrink: 0;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}

.tl-item.picked .tl-dot {
  background: var(--ios-green);
  box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.14);
}

.tl-item strong {
  font-size: 12.5px;
}

.tl-item p {
  margin: 2px 0 3px;
  font-size: 11.5px;
  color: var(--label-3);
}

.tl-time {
  font-size: 10.5px;
  color: var(--label-4);
}

@media (max-width: 980px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
