<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>异常处理</h1>
        <p>{{ summary.open }} 条待处理 · {{ summary.processing }} 条处理中 · 共 {{ summary.total }} 条</p>
      </div>
      <div class="head-actions">
        <el-button round :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <section class="stats">
      <article v-for="(item, i) in statCards" :key="item.label" class="stat card" v-reveal="i * 60">
        <div class="stat-icon" :style="{ background: item.tint, color: item.color }">
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-label">{{ item.label }}</span>
          <strong class="stat-value tabular">{{ item.value }}</strong>
          <span class="stat-hint">{{ item.hint }}</span>
        </div>
      </article>
    </section>

    <section class="toolbar card" v-reveal="80">
      <div class="seg" role="group" aria-label="异常状态筛选">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          :class="{ active: status === tab.value }"
          @click="switchStatus(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="toolbar-right">
        <el-select v-model="type" clearable placeholder="全部类型" class="type-select" @change="reload">
          <el-option v-for="t in types" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
        <el-input
          v-model="keyword"
          class="search"
          placeholder="运单号 / 收件人 / 手机号"
          clearable
          :prefix-icon="Search"
          @keyup.enter="reload"
          @clear="reload"
        />
      </div>
    </section>

    <section v-if="loading && !rows.length" class="list">
      <div v-for="i in 3" :key="i" class="card sk-card">
        <div class="sk-line w40"></div>
        <div class="sk-line w70"></div>
        <div class="sk-block"></div>
      </div>
    </section>

    <section v-else-if="!rows.length" class="empty card" v-reveal>
      <div class="empty-icon"><el-icon :size="26"><CircleCheck /></el-icon></div>
      <h3>{{ status ? '该状态下没有异常' : '当前没有异常件' }}</h3>
      <p>{{ status ? '切换上方分类看看。' : '包裹登记异常后会出现在这里。' }}</p>
    </section>

    <section v-else class="list">
      <article v-for="(item, i) in rows" :key="item.id" class="ex card" v-reveal="i * 60">
        <div class="ex-head">
          <span class="type-icon" :class="`t-${item.type}`">
            <el-icon :size="18"><component :is="iconOf(item.type)" /></el-icon>
          </span>
          <div class="ex-title">
            <strong class="mono">{{ item.tracking_no }}</strong>
            <span>{{ item.type_label }} · {{ item.station_name }}<template v-if="item.shelf_code"> · {{ item.shelf_code }} 货架</template></span>
          </div>
          <span class="pill" :class="`st-${item.status}`">{{ item.status_label }}</span>
        </div>

        <p class="desc">{{ item.description }}</p>

        <div class="ex-meta">
          <span>{{ item.recipient_name || '未匹配账号' }} · {{ mask(item.recipient_phone) }}</span>
          <span>{{ fmt(item.created_at) }}</span>
          <span v-if="item.handler_name">处理人 {{ item.handler_name }}</span>
        </div>

        <div class="ex-foot">
          <span class="pkg-state">包裹状态：{{ pkgLabel(item.package_status) }}</span>
          <span v-if="item.status === 'resolved'" class="done">
            已解决 · {{ fmt(item.resolved_at) }}
          </span>
          <button v-else class="mini primary" type="button" @click="openHandle(item)">处理</button>
        </div>
      </article>
    </section>

    <el-dialog v-model="dialogVisible" title="处理异常件" width="520px" :close-on-click-modal="false">
      <div v-if="active" class="dialog-body">
        <div class="dialog-pkg">
          <div>
            <strong class="mono">{{ active.tracking_no }}</strong>
            <span>{{ active.type_label }} · {{ active.station_name }}</span>
          </div>
          <span class="pill" :class="`st-${active.status}`">{{ active.status_label }}</span>
        </div>

        <el-form label-position="top">
          <el-form-item label="处理状态">
            <el-radio-group v-model="form.status">
              <el-radio value="processing">处理中</el-radio>
              <el-radio value="resolved">已解决</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.status === 'resolved'" label="包裹处理方式">
            <el-radio-group v-model="form.package_action" class="stack">
              <el-radio value="restock">重新入库（保留原格口）</el-radio>
              <el-radio value="returned">退回发件方（释放格口）</el-radio>
              <el-radio value="keep">保持异常（暂不处理包裹）</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="处理说明">
            <el-input
              v-model="form.remark"
              type="textarea"
              :rows="3"
              maxlength="200"
              show-word-limit
              placeholder="记录沟通结果或处理方式"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button round @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" round :loading="submitting" @click="submit">提交处理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, Search, Warning, Clock, CircleCheck, Bell, Box
} from '@element-plus/icons-vue'
import { exceptionSummary, handleException, listExceptions } from '../api/exceptions'

const rows = ref([])
const loading = ref(false)
const status = ref('')
const type = ref('')
const keyword = ref('')

const summary = reactive({ open: 0, processing: 0, resolved: 0, total: 0 })

const tabs = [
  { label: '全部', value: '' },
  { label: '待处理', value: 'open' },
  { label: '处理中', value: 'processing' },
  { label: '已解决', value: 'resolved' }
]

const types = [
  { label: '包装破损', value: 'damaged' },
  { label: '包裹丢失', value: 'lost' },
  { label: '错分驿站', value: 'wrong_station' },
  { label: '异常退回', value: 'returned' },
  { label: '其他异常', value: 'other' }
]

const statCards = computed(() => [
  { label: '待处理', value: summary.open, hint: '需要跟进', icon: Warning, tint: 'rgba(255,59,48,.1)', color: '#b3261e' },
  { label: '处理中', value: summary.processing, hint: '已受理', icon: Clock, tint: 'rgba(255,149,0,.14)', color: '#c26a00' },
  { label: '已解决', value: summary.resolved, hint: '处理完毕', icon: CircleCheck, tint: 'rgba(52,199,89,.13)', color: '#248a3d' },
  { label: '异常总数', value: summary.total, hint: '全部记录', icon: Bell, tint: 'rgba(0,122,255,.12)', color: '#007aff' }
])

function iconOf(value) {
  return { damaged: Warning, lost: Box, wrong_station: Box, returned: Box, other: Warning }[value] || Warning
}

function pkgLabel(value) {
  return {
    in_stock: '在库',
    picked: '已取件',
    overdue: '超期',
    returned: '已退回',
    exception: '异常'
  }[value] || value
}

function fmt(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function mask(phone) {
  return phone && phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone || '—'
}

async function load() {
  loading.value = true
  try {
    const [data, sum] = await Promise.all([
      listExceptions({
        page: 1,
        page_size: 50,
        status: status.value || undefined,
        type: type.value || undefined,
        keyword: keyword.value || undefined
      }),
      exceptionSummary()
    ])
    rows.value = data.items
    Object.assign(summary, sum)
  } finally {
    loading.value = false
  }
}

function switchStatus(value) {
  status.value = value
  load()
}

function reload() {
  load()
}

const dialogVisible = ref(false)
const active = ref(null)
const submitting = ref(false)
const form = reactive({ status: 'resolved', package_action: 'restock', remark: '' })

function openHandle(item) {
  active.value = item
  form.status = 'resolved'
  form.package_action = item.package_status === 'exception' ? 'restock' : 'keep'
  form.remark = ''
  dialogVisible.value = true
}

async function submit() {
  if (form.status === 'resolved' && form.package_action !== 'keep' && !form.remark.trim()) {
    ElMessage.warning('请填写处理说明')
    return
  }
  submitting.value = true
  try {
    const data = await handleException(active.value.id, {
      status: form.status,
      package_action: form.status === 'resolved' ? form.package_action : 'keep',
      remark: form.remark || undefined
    })
    ElMessage.success(data.status === 'resolved' ? '异常已解决' : '已转入处理中')
    dialogVisible.value = false
    await load()
  } finally {
    submitting.value = false
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
  grid-template-columns: repeat(4, 1fr);
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

.seg button.active {
  background: #fff;
  color: var(--label);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.toolbar-right {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.type-select {
  width: 140px;
}

.search {
  width: 230px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ex {
  padding: 20px 22px 16px;
  transition: transform 0.3s var(--spring), box-shadow 0.3s var(--ease);
}

.ex:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.ex-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.type-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(255, 59, 48, 0.1);
  color: #b3261e;
}

.type-icon.t-lost {
  background: rgba(175, 82, 222, 0.12);
  color: #8944ab;
}

.type-icon.t-wrong_station {
  background: rgba(255, 149, 0, 0.14);
  color: #c26a00;
}

.type-icon.t-returned {
  background: rgba(120, 120, 128, 0.12);
  color: var(--label-2);
}

.ex-title {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ex-title strong {
  font-size: 13.5px;
}

.ex-title span {
  font-size: 11.5px;
  color: var(--label-3);
}

.desc {
  margin: 0 0 12px;
  font-size: 12.5px;
  color: var(--label-2);
  line-height: 1.7;
  white-space: pre-wrap;
  background: var(--fill-2);
  border-radius: 12px;
  padding: 10px 12px;
}

.ex-meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--label-3);
  margin-bottom: 12px;
}

.ex-foot {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--separator);
}

.pkg-state {
  font-size: 11px;
  color: var(--label-3);
  margin-right: auto;
}

.done {
  font-size: 11px;
  color: #1d7a37;
}

.pill {
  display: inline-flex;
  align-items: center;
  height: 21px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
  flex-shrink: 0;
}

.st-open {
  background: rgba(255, 59, 48, 0.12);
  color: #b3261e;
}

.st-processing {
  background: rgba(255, 149, 0, 0.14);
  color: #a85900;
}

.st-resolved {
  background: rgba(52, 199, 89, 0.13);
  color: #1d7a37;
}

.mini {
  border: none;
  background: rgba(120, 120, 128, 0.1);
  color: var(--label-2);
  font-family: inherit;
  font-size: 11.5px;
  padding: 6px 14px;
  border-radius: 9px;
  cursor: pointer;
  transition: background 0.2s var(--ease), transform 0.2s var(--spring);
}

.mini.primary {
  background: var(--ios-blue);
  color: #fff;
  font-weight: 600;
}

.mini:active {
  transform: scale(0.94);
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
  background: rgba(52, 199, 89, 0.1);
  color: #248a3d;
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

.dialog-pkg {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--fill-2);
  margin-bottom: 16px;
}

.dialog-pkg div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dialog-pkg strong {
  font-size: 13px;
}

.dialog-pkg span {
  font-size: 11.5px;
  color: var(--label-3);
}

.stack :deep(.el-radio) {
  display: flex;
  height: 30px;
}

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
  height: 60px;
  border-radius: 12px;
}

.w40 { width: 40%; }
.w70 { width: 70%; }

@keyframes shimmer {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

@media (max-width: 1100px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
