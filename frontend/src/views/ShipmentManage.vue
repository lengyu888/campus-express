<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>寄件处理</h1>
        <p>{{ summary.pending }} 单待揽收 · {{ summary.accepted }} 单待发出 · {{ summary.shipped }} 单运输中</p>
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
      <div class="seg" role="group" aria-label="订单状态筛选">
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
      <el-input
        v-model="keyword"
        class="search"
        placeholder="订单号 / 收件人 / 物品"
        clearable
        :prefix-icon="Search"
        @keyup.enter="reload"
        @clear="reload"
      />
    </section>

    <section class="table-card card" v-reveal="140">
      <el-table v-loading="loading" :data="rows" class="ship-table" @row-click="openDetail">
        <el-table-column label="订单号" min-width="170">
          <template #default="{ row }">
            <div class="cell-main mono">{{ row.order_no }}</div>
            <div class="cell-sub">{{ row.created_at ? fmt(row.created_at) : '' }}</div>
          </template>
        </el-table-column>

        <el-table-column label="寄件人" min-width="130">
          <template #default="{ row }">
            <div class="cell-main">{{ row.sender_name }}</div>
            <div class="cell-sub">{{ row.sender_no || row.sender_phone }}</div>
          </template>
        </el-table-column>

        <el-table-column label="收件人" min-width="180">
          <template #default="{ row }">
            <div class="cell-main">{{ row.receiver_name }} · {{ mask(row.receiver_phone) }}</div>
            <div class="cell-sub ellipsis">{{ row.receiver_address }}</div>
          </template>
        </el-table-column>

        <el-table-column label="物品" min-width="130">
          <template #default="{ row }">
            <div class="cell-main">{{ row.item_name }}</div>
            <div class="cell-sub tabular">{{ row.weight }} kg · ¥{{ row.freight }}</div>
          </template>
        </el-table-column>

        <el-table-column label="交寄驿站" width="112">
          <template #default="{ row }">
            <span class="cell-main">{{ row.station_name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="98">
          <template #default="{ row }">
            <span class="pill" :class="`st-${row.status}`">{{ row.status_label }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" align="right">
          <template #default="{ row }">
            <div class="row-actions" @click.stop>
              <button v-if="row.status === 'pending'" class="mini primary" type="button"
                      @click="openAccept(row)">揽收</button>
              <button v-else-if="row.status === 'accepted'" class="mini primary" type="button"
                      @click="doShip(row)">发出</button>
              <button v-else-if="row.status === 'shipped'" class="mini primary" type="button"
                      @click="doComplete(row)">完成</button>
              <button class="mini" type="button" @click="openDetail(row)">详情</button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !rows.length" class="empty">
        <div class="empty-icon"><el-icon :size="26"><Van /></el-icon></div>
        <h3>没有符合条件的寄件订单</h3>
        <p>学生下单后会出现在这里。</p>
      </div>

      <div v-if="total > 0" class="table-foot">
        <span class="foot-total">共 {{ total }} 单</span>
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

    <el-dialog v-model="acceptVisible" title="驿站揽收" width="440px" :close-on-click-modal="false">
      <p class="dialog-tip">{{ active?.order_no }} · {{ active?.receiver_name }} · {{ active?.item_name }}</p>

      <el-form label-position="top">
        <el-form-item label="实际重量（kg）">
          <el-input-number v-model="acceptForm.weight" :min="0.1" :max="999" :precision="1"
                           :step="0.5" style="width: 100%" />
        </el-form-item>
        <el-form-item label="快递公司">
          <el-select v-model="acceptForm.courier_company" clearable placeholder="选择承运商" style="width: 100%">
            <el-option v-for="c in couriers" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="运费（元）">
          <el-input-number v-model="acceptForm.freight" :min="0" :max="9999" :precision="2"
                           :step="1" style="width: 100%" />
        </el-form-item>
      </el-form>

      <div class="freight-hint">
        按重量自动估算 ¥{{ estimate.toFixed(2) }}（首重 8 元 + 续重 2 元/kg），可手动调整。
      </div>

      <template #footer>
        <el-button round @click="acceptVisible = false">取消</el-button>
        <el-button type="primary" round :loading="acting" @click="submitAccept">确认揽收</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" :with-header="false" size="460px">
      <div v-if="detail" class="detail">
        <div class="drawer-head">
          <div>
            <h3 class="mono">{{ detail.order_no }}</h3>
            <span>{{ detail.item_name }} · {{ detail.weight }} kg · ¥{{ detail.freight }}</span>
          </div>
          <button class="drawer-close" type="button" aria-label="关闭" @click="detailVisible = false">
            <el-icon :size="16"><Close /></el-icon>
          </button>
        </div>

        <div class="detail-status">
          <span class="pill" :class="`st-${detail.status}`">{{ detail.status_label }}</span>
          <span>{{ detail.sender_name }} · {{ detail.sender_no || detail.sender_phone }}</span>
        </div>

        <dl class="detail-grid">
          <div><dt>寄件驿站</dt><dd>{{ detail.station_name }}</dd></div>
          <div><dt>快递公司</dt><dd>{{ detail.courier_company || '待确认' }}</dd></div>
          <div><dt>收件人</dt><dd>{{ detail.receiver_name }}</dd></div>
          <div><dt>联系电话</dt><dd class="tabular">{{ detail.receiver_phone }}</dd></div>
          <div class="full"><dt>收件地址</dt><dd>{{ detail.receiver_address }}</dd></div>
          <div><dt>下单时间</dt><dd class="mono small">{{ fmt(detail.created_at) }}</dd></div>
          <div><dt>运费</dt><dd class="tabular">¥{{ detail.freight }}</dd></div>
        </dl>

        <div v-if="detail.remark" class="detail-remark">{{ detail.remark }}</div>

        <h4 class="timeline-title">物流轨迹</h4>
        <div class="timeline">
          <div v-for="(track, i) in detail.tracks" :key="i" class="tl-item" :class="`is-${track.status}`">
            <span class="tl-dot"></span>
            <div>
              <strong>{{ track.node }}</strong>
              <p>{{ track.description }}</p>
              <span class="tl-time mono">{{ fmt(track.occurred_at) }}
                <template v-if="track.operator_name"> · {{ track.operator_name }}</template>
              </span>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <el-button v-if="detail.status === 'pending'" type="primary" round @click="openAccept(detail)">
            揽收
          </el-button>
          <el-button v-if="detail.status === 'accepted'" type="primary" round @click="doShip(detail)">
            登记发出
          </el-button>
          <el-button v-if="detail.status === 'shipped'" type="primary" round @click="doComplete(detail)">
            确认完成
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Search, Van, Clock, CircleCheck, Box, Close
} from '@element-plus/icons-vue'
import {
  acceptShipment, completeShipment, getShipment, listShipments, shipmentsSummary, shipShipment
} from '../api/shipments'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)
const status = ref('')
const keyword = ref('')
const summary = reactive({ pending: 0, accepted: 0, shipped: 0, completed: 0, cancelled: 0, total: 0 })
const couriers = ['顺丰速运', '京东物流', '圆通速递', '中通快递', '申通快递', '韵达快递', 'EMS', '极兔速递']

const tabs = [
  { label: '全部', value: '' },
  { label: '待揽收', value: 'pending' },
  { label: '已揽收', value: 'accepted' },
  { label: '已发出', value: 'shipped' },
  { label: '已完成', value: 'completed' }
]

const statCards = computed(() => [
  { label: '待揽收', value: summary.pending, hint: '等待学生交寄', icon: Clock, tint: 'rgba(255,149,0,.14)', color: '#c26a00' },
  { label: '已揽收', value: summary.accepted, hint: '待登记发出', icon: Box, tint: 'rgba(0,122,255,.12)', color: '#007aff' },
  { label: '已发出', value: summary.shipped, hint: '运输中', icon: Van, tint: 'rgba(48,176,199,.14)', color: '#0b6b7d' },
  { label: '已完成', value: summary.completed, hint: '已签收', icon: CircleCheck, tint: 'rgba(52,199,89,.13)', color: '#248a3d' }
])

function fmt(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function mask(phone) {
  return phone && phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone
}

async function load() {
  loading.value = true
  try {
    const [data, sum] = await Promise.all([
      listShipments({
        page: page.value,
        page_size: pageSize,
        status: status.value || undefined,
        keyword: keyword.value || undefined
      }),
      shipmentsSummary()
    ])
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

function switchStatus(value) {
  status.value = value
  reload()
}

/* 揽收 */
const acceptVisible = ref(false)
const active = ref(null)
const acting = ref(false)
const acceptForm = reactive({ weight: 1, courier_company: '', freight: 0 })

const estimate = computed(() => {
  const w = Number(acceptForm.weight) || 0
  if (w <= 0) return 0
  return 8 + 2 * (Math.ceil(w) - 1)
})

function openAccept(row) {
  active.value = row
  acceptForm.weight = Number(row.weight) || 1
  acceptForm.courier_company = row.courier_company || ''
  acceptForm.freight = Number(row.freight) || estimate.value
  acceptVisible.value = true
}

async function submitAccept() {
  acting.value = true
  try {
    await acceptShipment(active.value.id, {
      weight: acceptForm.weight,
      courier_company: acceptForm.courier_company || undefined,
      freight: acceptForm.freight
    })
    ElMessage.success('揽收成功，运费已确认')
    acceptVisible.value = false
    detailVisible.value = false
    await load()
  } finally {
    acting.value = false
  }
}

async function doShip(row) {
  try {
    await ElMessageBox.confirm(`确认 ${row.order_no} 已交由承运商发出？`, '登记发出', {
      confirmButtonText: '确认发出', cancelButtonText: '取消'
    })
  } catch (e) {
    return
  }
  await shipShipment(row.id)
  ElMessage.success('已登记发出')
  detailVisible.value = false
  await load()
}

async function doComplete(row) {
  try {
    await ElMessageBox.confirm(`确认 ${row.order_no} 已被收件人签收？`, '确认完成', {
      confirmButtonText: '确认完成', cancelButtonText: '取消'
    })
  } catch (e) {
    return
  }
  await completeShipment(row.id)
  ElMessage.success('订单已完成')
  detailVisible.value = false
  await load()
}

/* 详情 */
const detailVisible = ref(false)
const detail = ref(null)

async function openDetail(row) {
  const data = await getShipment(row.id)
  detail.value = data
  detailVisible.value = true
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
  padding: 7px 14px;
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

.search {
  width: 240px;
}

.table-card {
  padding: 6px 8px 8px;
  overflow: hidden;
}

.ship-table {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(0, 122, 255, 0.045);
  background: transparent;
}

.ship-table :deep(th.el-table__cell) {
  background: transparent;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--label-3);
  border-bottom: 1px solid var(--separator);
  padding: 12px 0;
}

.ship-table :deep(td.el-table__cell) {
  border-bottom: 1px solid var(--separator);
  padding: 13px 0;
}

.ship-table :deep(.el-table__row) {
  cursor: pointer;
}

.cell-main {
  font-size: 12.8px;
  color: var(--label);
  font-weight: 550;
}

.cell-sub {
  margin-top: 3px;
  font-size: 11px;
  color: var(--label-3);
}

.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 190px;
}

.mono {
  font-family: 'SF Mono', 'JetBrains Mono', Consolas, monospace;
}

.small {
  font-size: 11.5px;
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

.st-pending {
  background: rgba(255, 149, 0, 0.14);
  color: #a85900;
}

.st-accepted {
  background: rgba(0, 122, 255, 0.1);
  color: #0a5bb5;
}

.st-shipped {
  background: rgba(48, 176, 199, 0.14);
  color: #0b6b7d;
}

.st-completed {
  background: rgba(52, 199, 89, 0.13);
  color: #1d7a37;
}

.st-cancelled {
  background: rgba(120, 120, 128, 0.13);
  color: var(--label-2);
}

.row-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.mini {
  border: none;
  background: rgba(120, 120, 128, 0.1);
  color: var(--label-2);
  font-family: inherit;
  font-size: 11.5px;
  padding: 5px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s var(--ease), transform 0.2s var(--spring);
}

.mini:hover {
  background: rgba(120, 120, 128, 0.16);
}

.mini:active {
  transform: scale(0.93);
}

.mini.primary {
  background: var(--ios-blue);
  color: #fff;
  font-weight: 600;
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

.dialog-tip {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--label-3);
}

.freight-hint {
  font-size: 11.5px;
  color: var(--label-3);
  background: rgba(0, 122, 255, 0.06);
  border-radius: 12px;
  padding: 10px 12px;
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
  margin: 0 0 6px;
}

.detail-grid .full {
  grid-column: 1 / -1;
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

.detail-remark {
  font-size: 12px;
  color: var(--label-2);
  background: rgba(255, 149, 0, 0.09);
  border-radius: 12px;
  padding: 10px 12px;
  margin: 12px 0;
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
  background: #d1d1d6;
  margin-top: 5px;
  flex-shrink: 0;
}

.tl-item.is-pending .tl-dot {
  background: var(--ios-orange);
  box-shadow: 0 0 0 3px rgba(255, 149, 0, 0.14);
}

.tl-item.is-accepted .tl-dot,
.tl-item.is-shipped .tl-dot {
  background: var(--ios-blue);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}

.tl-item.is-completed .tl-dot {
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

.detail-actions {
  display: flex;
  gap: 8px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--separator);
}

@media (max-width: 1100px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
