<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>我的寄件</h1>
        <p>{{ summary.total }} 单寄件 · {{ summary.pending }} 单待揽收 · {{ summary.completed }} 单已完成</p>
      </div>
      <div class="head-actions">
        <el-button round :icon="Refresh" :loading="loading" @click="reload">刷新</el-button>
        <el-button type="primary" round :icon="Plus" @click="openCreate">新建寄件</el-button>
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
      <div class="seg" role="group" aria-label="寄件状态筛选">
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
      <span class="toolbar-note">运费首重 8 元 / 1kg，续重 2 元 / kg，线下结算</span>
    </section>

    <section v-if="loading && !rows.length" class="grid">
      <div v-for="i in 4" :key="i" class="card sk-card">
        <div class="sk-line w40"></div>
        <div class="sk-line w70"></div>
        <div class="sk-block"></div>
      </div>
    </section>

    <section v-else-if="!rows.length" class="empty card" v-reveal>
      <div class="empty-icon"><el-icon :size="26"><Van /></el-icon></div>
      <h3>{{ status ? '该状态下没有订单' : '还没有寄件订单' }}</h3>
      <p>{{ status ? '切换上方分类看看。' : '填写收件信息后，到驿站交寄即可。' }}</p>
      <el-button v-if="!status" type="primary" round :icon="Plus" @click="openCreate">新建寄件</el-button>
    </section>

    <section v-else class="grid">
      <article
        v-for="(order, i) in rows"
        :key="order.id"
        class="order card"
        v-reveal="i * 60"
        @click="openDetail(order)"
      >
        <div class="order-head">
          <span class="order-no mono">{{ order.order_no }}</span>
          <span class="pill" :class="`st-${order.status}`">{{ order.status_label }}</span>
        </div>

        <div class="route">
          <div class="route-point">
            <span class="dot"></span>
            <div>
              <strong>{{ order.station_name }}</strong>
              <span>校园驿站</span>
            </div>
          </div>
          <div class="route-line"></div>
          <div class="route-point">
            <span class="dot end"></span>
            <div>
              <strong>{{ order.receiver_name }} · {{ mask(order.receiver_phone) }}</strong>
              <span class="addr">{{ order.receiver_address }}</span>
            </div>
          </div>
        </div>

        <div class="order-meta">
          <span class="meta-item">{{ order.item_name }}</span>
          <span class="meta-item tabular">{{ order.weight }} kg</span>
          <span class="meta-item price tabular">¥{{ order.freight }}</span>
          <span v-if="order.courier_company" class="meta-item">{{ order.courier_company }}</span>
        </div>

        <div class="order-foot">
          <span class="time">{{ fmt(order.created_at) }} · {{ order.latest_track || '已创建' }}</span>
          <div class="actions">
            <button v-if="order.status === 'pending'" class="link danger" type="button"
                    @click.stop="cancel(order)">取消订单</button>
            <button class="link" type="button" @click.stop="openDetail(order)">
              查看轨迹
              <el-icon :size="12"><ArrowRight /></el-icon>
            </button>
          </div>
        </div>
      </article>
    </section>

    <el-drawer v-model="createVisible" :with-header="false" size="520px" @closed="resetForm">
      <div class="drawer-head">
        <div>
          <h3>新建寄件</h3>
          <span>填写收件信息，系统按重量估算运费</span>
        </div>
        <button class="drawer-close" type="button" aria-label="关闭" @click="createVisible = false">
          <el-icon :size="16"><Close /></el-icon>
        </button>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="ship-form">
        <el-form-item label="交寄驿站" prop="station_id">
          <el-select v-model="form.station_id" placeholder="选择驿站" style="width: 100%">
            <el-option
              v-for="s in stations"
              :key="s.id"
              :label="`${s.name}（${s.open_time}—${s.close_time}）`"
              :value="s.id"
              :disabled="s.status === 0"
            />
          </el-select>
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="收件人姓名" prop="receiver_name">
            <el-input v-model="form.receiver_name" maxlength="50" placeholder="收件人" />
          </el-form-item>
          <el-form-item label="收件人手机号" prop="receiver_phone">
            <el-input v-model="form.receiver_phone" maxlength="11" placeholder="11 位手机号" />
          </el-form-item>
        </div>

        <el-form-item label="收件地址" prop="receiver_address">
          <el-input v-model="form.receiver_address" type="textarea" :rows="2" maxlength="200"
                    placeholder="省市区 + 详细地址" />
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="物品名称" prop="item_name">
            <el-input v-model="form.item_name" maxlength="100" placeholder="如：书籍" />
          </el-form-item>
          <el-form-item label="重量（kg）" prop="weight">
            <el-input-number v-model="form.weight" :min="0.1" :max="999" :precision="1"
                             :step="0.5" style="width: 100%" />
          </el-form-item>
        </div>

        <el-form-item label="快递公司">
          <el-select v-model="form.courier_company" clearable placeholder="选填，揽收时确认" style="width: 100%">
            <el-option v-for="c in couriers" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="255"
                    placeholder="如：易碎，请轻放" />
        </el-form-item>

        <div class="freight-box">
          <div>
            <span>预估运费</span>
            <strong class="tabular">¥{{ estimate.toFixed(2) }}</strong>
          </div>
          <p>首重 1kg 8 元，续重每 kg 加 2 元，实际以驿站称重为准</p>
        </div>

        <el-button type="primary" round class="submit" :loading="submitting" @click="submit">
          提交寄件订单
        </el-button>
      </el-form>
    </el-drawer>

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
          <span>{{ statusHint(detail) }}</span>
        </div>

        <div class="detail-route">
          <div class="route-point">
            <span class="dot"></span>
            <div><strong>{{ detail.station_name }}</strong><span>交寄驿站</span></div>
          </div>
          <div class="route-line"></div>
          <div class="route-point">
            <span class="dot end"></span>
            <div>
              <strong>{{ detail.receiver_name }} · {{ detail.receiver_phone }}</strong>
              <span class="addr">{{ detail.receiver_address }}</span>
            </div>
          </div>
        </div>

        <dl class="detail-grid">
          <div><dt>快递公司</dt><dd>{{ detail.courier_company || '待确认' }}</dd></div>
          <div><dt>运费</dt><dd class="tabular">¥{{ detail.freight }}</dd></div>
          <div><dt>下单时间</dt><dd class="mono small">{{ fmt(detail.created_at) }}</dd></div>
          <div><dt>最近节点</dt><dd>{{ detail.latest_track || '—' }}</dd></div>
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

        <el-button
          v-if="detail.status === 'pending'"
          round
          class="cancel-btn"
          @click="cancel(detail)"
        >
          取消订单
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Plus, Van, Clock, CircleCheck, Box, Close, ArrowRight, Warning
} from '@element-plus/icons-vue'
import {
  cancelShipment, createShipment, getShipment, listShipments, shipmentsSummary
} from '../api/shipments'
import { listStations } from '../api/stations'

const rows = ref([])
const loading = ref(false)
const status = ref('')
const stations = ref([])
const couriers = ['顺丰速运', '京东物流', '圆通速递', '中通快递', '申通快递', '韵达快递', 'EMS', '极兔速递']

const summary = reactive({ pending: 0, accepted: 0, shipped: 0, completed: 0, cancelled: 0, total: 0 })

const tabs = [
  { label: '全部', value: '' },
  { label: '待揽收', value: 'pending' },
  { label: '已揽收', value: 'accepted' },
  { label: '已发出', value: 'shipped' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' }
]

const statCards = computed(() => [
  { label: '待揽收', value: summary.pending, hint: '等待交寄', icon: Clock, tint: 'rgba(255,149,0,.14)', color: '#c26a00' },
  { label: '运输中', value: summary.accepted + summary.shipped, hint: '已揽收 / 已发出', icon: Van, tint: 'rgba(0,122,255,.12)', color: '#007aff' },
  { label: '已完成', value: summary.completed, hint: '已签收', icon: CircleCheck, tint: 'rgba(52,199,89,.13)', color: '#248a3d' },
  { label: '累计订单', value: summary.total, hint: '全部记录', icon: Box, tint: 'rgba(175,82,222,.12)', color: '#8944ab' }
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

function statusHint(order) {
  const map = {
    pending: '请携带物品到所选驿站交寄',
    accepted: '驿站已揽收，等待发出',
    shipped: '包裹运输中',
    completed: '收件人已签收',
    cancelled: '订单已取消'
  }
  return map[order.status] || ''
}

async function load() {
  loading.value = true
  try {
    const [data, sum] = await Promise.all([
      listShipments({ page: 1, page_size: 50, status: status.value || undefined }),
      shipmentsSummary()
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

async function reload() {
  await load()
}

/* 新建 */
const createVisible = ref(false)
const formRef = ref()
const submitting = ref(false)
const form = reactive({
  station_id: null,
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
  item_name: '',
  weight: 1,
  courier_company: '',
  remark: ''
})

const rules = {
  station_id: [{ required: true, message: '请选择交寄驿站', trigger: 'change' }],
  receiver_name: [{ required: true, message: '请填写收件人姓名', trigger: 'blur' }],
  receiver_phone: [
    { required: true, message: '请填写收件人手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  receiver_address: [{ required: true, min: 5, message: '请填写完整收件地址', trigger: 'blur' }],
  item_name: [{ required: true, message: '请填写物品名称', trigger: 'blur' }],
  weight: [{ required: true, message: '请填写重量', trigger: 'change' }]
}

const estimate = computed(() => {
  const w = Number(form.weight) || 0
  if (w <= 0) return 0
  return 8 + 2 * (Math.ceil(w) - 1)
})

function openCreate() {
  createVisible.value = true
  if (!form.station_id && stations.value.length) {
    form.station_id = stations.value[0].id
  }
}

function resetForm() {
  Object.assign(form, {
    station_id: stations.value[0]?.id || null,
    receiver_name: '',
    receiver_phone: '',
    receiver_address: '',
    item_name: '',
    weight: 1,
    courier_company: '',
    remark: ''
  })
  formRef.value?.clearValidate()
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await createShipment({ ...form, courier_company: form.courier_company || undefined })
    ElMessage.success('寄件订单已创建，请到驿站交寄')
    createVisible.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

/* 详情 */
const detailVisible = ref(false)
const detail = ref(null)

async function openDetail(order) {
  const data = await getShipment(order.id)
  detail.value = data
  detailVisible.value = true
}

async function cancel(order) {
  try {
    await ElMessageBox.confirm(
      `确认取消订单 ${order.order_no} 吗？取消后需重新下单。`,
      '取消订单',
      { confirmButtonText: '确认取消', cancelButtonText: '再想想', type: 'warning' }
    )
  } catch (e) {
    return
  }
  await cancelShipment(order.id)
  ElMessage.success('订单已取消')
  detailVisible.value = false
  await load()
}

onMounted(async () => {
  const data = await listStations()
  stations.value = data.items
  await load()
})
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
  transition: transform 0.3s var(--spring), box-shadow 0.3s var(--ease);
}

.stat:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
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
  flex-wrap: wrap;
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

.order {
  padding: 20px 22px 16px;
  cursor: pointer;
  transition: transform 0.32s var(--spring), box-shadow 0.3s var(--ease);
}

.order:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.order-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.order-no {
  font-size: 13px;
  font-weight: 650;
  letter-spacing: 0.02em;
}

.route {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 14px;
}

.route-point {
  display: flex;
  gap: 11px;
  align-items: flex-start;
}

.route-point .dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 2px solid var(--ios-blue);
  background: #fff;
  margin-top: 5px;
  flex-shrink: 0;
}

.route-point .dot.end {
  border-color: var(--ios-green);
  background: var(--ios-green);
}

.route-point div {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.route-point strong {
  font-size: 12.8px;
  font-weight: 600;
}

.route-point span {
  font-size: 11px;
  color: var(--label-3);
  margin-top: 2px;
}

.route-point .addr {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 320px;
}

.route-line {
  width: 1px;
  height: 16px;
  background: var(--separator);
  margin-left: 4px;
  margin: 2px 0 2px 4px;
}

.order-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: 14px;
}

.meta-item {
  font-size: 11px;
  color: var(--label-2);
  background: var(--fill-2);
  padding: 4px 9px;
  border-radius: 999px;
}

.meta-item.price {
  color: #a85900;
  background: rgba(255, 149, 0, 0.12);
  font-weight: 600;
}

.order-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid var(--separator);
}

.time {
  font-size: 10.8px;
  color: var(--label-4);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
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
  padding: 3px 2px;
  transition: gap 0.25s var(--ease), opacity 0.2s;
}

.link:hover {
  gap: 7px;
}

.link.danger {
  color: var(--ios-red);
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
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--label-3);
}

.mono {
  font-family: 'SF Mono', 'JetBrains Mono', Consolas, monospace;
}

.small {
  font-size: 11.5px;
}

/* 抽屉表单 */
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}

.drawer-head h3 {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
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

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.ship-form :deep(.el-form-item__label) {
  font-size: 12px;
  color: var(--label-2);
  padding-bottom: 5px;
}

.freight-box {
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.08), rgba(94, 92, 230, 0.1));
  padding: 14px 16px;
  margin: 6px 0 18px;
}

.freight-box div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.freight-box span {
  font-size: 11.5px;
  color: var(--label-3);
}

.freight-box strong {
  font-size: 26px;
  color: #0a5bb5;
  letter-spacing: -0.02em;
}

.freight-box p {
  margin: 4px 0 0;
  font-size: 10.5px;
  color: var(--label-3);
}

.submit {
  width: 100%;
  height: 46px;
  font-weight: 600;
}

/* 详情 */
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

.detail-route {
  margin-bottom: 18px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  margin: 0 0 6px;
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

.cancel-btn {
  width: 100%;
  margin-top: 22px;
  color: var(--ios-red);
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
  height: 76px;
  border-radius: 16px;
}

.w40 { width: 40%; }
.w70 { width: 70%; }

@keyframes shimmer {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

@media (max-width: 980px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
