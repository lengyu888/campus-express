<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>操作日志</h1>
        <p>共 {{ summary.total }} 条操作记录 · 今日 {{ summary.today }} 条</p>
      </div>
      <div class="head-actions">
        <el-button round :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <section class="stats">
      <article class="stat card" v-reveal>
        <div class="stat-icon blue"><el-icon :size="18"><Document /></el-icon></div>
        <div class="stat-body">
          <span class="stat-label">操作总数</span>
          <strong class="stat-value tabular">{{ summary.total }}</strong>
          <span class="stat-hint">已记录写操作</span>
        </div>
      </article>
      <article class="stat card" v-reveal="60">
        <div class="stat-icon green"><el-icon :size="18"><Clock /></el-icon></div>
        <div class="stat-body">
          <span class="stat-label">今日操作</span>
          <strong class="stat-value tabular">{{ summary.today }}</strong>
          <span class="stat-hint">当日新增</span>
        </div>
      </article>
      <article class="stat card" v-reveal="120">
        <div class="stat-icon purple"><el-icon :size="18"><Grid /></el-icon></div>
        <div class="stat-body">
          <span class="stat-label">涉及模块</span>
          <strong class="stat-value tabular">{{ summary.modules.length }}</strong>
          <span class="stat-hint">业务模块数</span>
        </div>
      </article>
    </section>

    <section class="toolbar card" v-reveal="80">
      <div class="chips">
        <button type="button" class="chip" :class="{ active: module === '' }" @click="switchModule('')">
          全部
        </button>
        <button
          v-for="m in summary.modules"
          :key="m.module"
          type="button"
          class="chip"
          :class="{ active: module === m.module }"
          @click="switchModule(m.module)"
        >
          {{ m.label }}
          <span class="chip-count">{{ m.count }}</span>
        </button>
      </div>
      <div class="toolbar-right">
        <el-date-picker
          v-model="range"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          class="date-range"
          @change="reload"
        />
        <el-input
          v-model="keyword"
          class="search"
          placeholder="操作人姓名 / 学号"
          clearable
          :prefix-icon="Search"
          @keyup.enter="reload"
          @clear="reload"
        />
      </div>
    </section>

    <section class="table-card card" v-reveal="140">
      <el-table v-loading="loading" :data="rows" class="log-table">
        <el-table-column label="时间" width="150">
          <template #default="{ row }">
            <span class="mono small">{{ fmt(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作人" width="150">
          <template #default="{ row }">
            <div class="cell-main">{{ row.user_name }}</div>
            <div class="cell-sub">{{ roleLabel(row.user_role) }}</div>
          </template>
        </el-table-column>

        <el-table-column label="模块" width="110">
          <template #default="{ row }">
            <span class="module-tag">{{ row.module_label }}</span>
          </template>
        </el-table-column>

        <el-table-column label="动作" width="120">
          <template #default="{ row }">
            <span class="action">{{ row.action_label }}</span>
          </template>
        </el-table-column>

        <el-table-column label="对象" width="110">
          <template #default="{ row }">
            <span v-if="row.target_id" class="mono small">#{{ row.target_id }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="请求" min-width="240">
          <template #default="{ row }">
            <div class="request">
              <span class="method" :class="methodClass(row.detail?.method)">{{ row.detail?.method }}</span>
              <span class="mono path">{{ row.detail?.path }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="IP" width="130">
          <template #default="{ row }">
            <span class="mono small muted">{{ row.ip || '—' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !rows.length" class="empty">
        <div class="empty-icon"><el-icon :size="26"><Document /></el-icon></div>
        <h3>暂无操作记录</h3>
        <p>系统中的新增、修改、删除等写操作会自动记录在这里。</p>
      </div>

      <div v-if="total > 0" class="table-foot">
        <span class="foot-total">共 {{ total }} 条</span>
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          background
          @current-change="load"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Refresh, Search, Document, Clock, Grid } from '@element-plus/icons-vue'
import { listLogs, logSummary } from '../api/logs'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 15
const loading = ref(false)
const module = ref('')
const keyword = ref('')
const range = ref(null)

const summary = reactive({ total: 0, today: 0, modules: [] })

function fmt(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function roleLabel(role) {
  return { admin: '管理员', staff: '工作人员', student: '学生' }[role] || '系统'
}

function methodClass(method) {
  return {
    POST: 'post',
    PUT: 'put',
    PATCH: 'patch',
    DELETE: 'delete'
  }[method] || ''
}

async function load() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
      module: module.value || undefined,
      keyword: keyword.value || undefined
    }
    if (range.value?.length === 2) {
      params.start = range.value[0]
      params.end = range.value[1]
    }
    const [data, sum] = await Promise.all([listLogs(params), logSummary()])
    rows.value = data.items
    total.value = data.total
    Object.assign(summary, sum)
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  load()
}

function switchModule(value) {
  module.value = value
  reload()
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

.stat-icon.green {
  background: rgba(52, 199, 89, 0.13);
  color: #248a3d;
}

.stat-icon.purple {
  background: rgba(175, 82, 222, 0.12);
  color: #8944ab;
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

.chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: none;
  background: var(--fill-2);
  color: var(--label-2);
  font-family: inherit;
  font-size: 11.5px;
  padding: 6px 12px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.25s var(--ease);
}

.chip.active {
  background: rgba(0, 122, 255, 0.1);
  color: #0a5bb5;
  font-weight: 600;
}

.chip-count {
  font-size: 10px;
  color: var(--label-4);
  font-variant-numeric: tabular-nums;
}

.chip.active .chip-count {
  color: #0a5bb5;
}

.toolbar-right {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.date-range {
  width: 240px;
}

.search {
  width: 200px;
}

.table-card {
  padding: 6px 8px 8px;
  overflow: hidden;
}

.log-table {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(0, 122, 255, 0.045);
  background: transparent;
}

.log-table :deep(th.el-table__cell) {
  background: transparent;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--label-3);
  border-bottom: 1px solid var(--separator);
  padding: 12px 0;
}

.log-table :deep(td.el-table__cell) {
  border-bottom: 1px solid var(--separator);
  padding: 12px 0;
}

.cell-main {
  font-size: 12.8px;
  font-weight: 550;
}

.cell-sub {
  margin-top: 2px;
  font-size: 10.8px;
  color: var(--label-3);
}

.module-tag {
  display: inline-flex;
  align-items: center;
  height: 21px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 10.8px;
  font-weight: 600;
  background: rgba(0, 122, 255, 0.08);
  color: #0a5bb5;
}

.action {
  font-size: 12px;
  color: var(--label);
  font-weight: 550;
}

.request {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.method {
  font-size: 9.5px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 5px;
  background: var(--fill-2);
  color: var(--label-2);
  flex-shrink: 0;
}

.method.post {
  background: rgba(52, 199, 89, 0.13);
  color: #1d7a37;
}

.method.put,
.method.patch {
  background: rgba(255, 149, 0, 0.14);
  color: #a85900;
}

.method.delete {
  background: rgba(255, 59, 48, 0.12);
  color: #b3261e;
}

.path {
  font-size: 11px;
  color: var(--label-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mono {
  font-family: 'SF Mono', 'JetBrains Mono', Consolas, monospace;
}

.small {
  font-size: 11.5px;
}

.muted {
  color: var(--label-4);
}

.table-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 14px 8px;
}

.foot-total {
  font-size: 12px;
  color: var(--label-3);
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 54px 20px 58px;
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

@media (max-width: 1100px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
