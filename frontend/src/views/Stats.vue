<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>统计报表</h1>
        <p>收发量、超期情况与驿站工作量</p>
      </div>
      <div class="head-actions">
        <div class="seg small">
          <button
            v-for="d in [7, 14, 30]"
            :key="d"
            type="button"
            :class="{ active: days === d }"
            @click="switchDays(d)"
          >
            近 {{ d }} 天
          </button>
        </div>
        <el-button round :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <section class="kpis">
      <article v-for="(item, i) in kpis" :key="item.label" class="kpi card" v-reveal="i * 50">
        <div class="kpi-top">
          <span class="kpi-label">{{ item.label }}</span>
          <span class="kpi-icon" :style="{ background: item.tint, color: item.color }">
            <el-icon :size="15"><component :is="item.icon" /></el-icon>
          </span>
        </div>
        <strong class="kpi-value tabular">{{ item.value }}</strong>
        <span class="kpi-hint">{{ item.hint }}</span>
      </article>
    </section>

    <section class="panel card" v-reveal="120">
      <div class="panel-head">
        <div>
          <h3>收发量趋势</h3>
          <p>近 {{ days }} 天入库与出库件数</p>
        </div>
        <div class="legend">
          <span><i class="dot inbound"></i>入库 {{ trend.inbound_total || 0 }}</span>
          <span><i class="dot picked"></i>出库 {{ trend.picked_total || 0 }}</span>
        </div>
      </div>

      <svg class="chart" viewBox="0 0 720 220" role="img" aria-label="收发量趋势图">
        <defs>
          <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="rgba(0,122,255,0.26)" />
            <stop offset="100%" stop-color="rgba(0,122,255,0)" />
          </linearGradient>
        </defs>

        <g class="grid">
          <line v-for="g in gridLines" :key="g.y" :x1="34" :x2="704" :y1="g.y" :y2="g.y" />
          <text v-for="g in gridLines" :key="`t-${g.y}`" :x="26" :y="g.y + 3" text-anchor="end">{{ g.label }}</text>
        </g>

        <path v-if="chart.areaInbound" :d="chart.areaInbound" fill="url(#areaFill)" />
        <path v-if="chart.lineInbound" :d="chart.lineInbound" class="line inbound" />
        <path v-if="chart.linePicked" :d="chart.linePicked" class="line picked" />

        <g v-for="(p, i) in chart.inboundPoints" :key="`pi-${i}`">
          <circle :cx="p[0]" :cy="p[1]" r="3.2" class="point inbound" />
          <title>{{ trend.items[i].label }} 入库 {{ trend.items[i].inbound }} 件</title>
        </g>
        <g v-for="(p, i) in chart.pickedPoints" :key="`pp-${i}`">
          <circle :cx="p[0]" :cy="p[1]" r="2.8" class="point picked" />
          <title>{{ trend.items[i].label }} 出库 {{ trend.items[i].picked }} 件</title>
        </g>

        <g class="axis">
          <text
            v-for="(item, i) in trend.items"
            :key="`x-${i}`"
            :x="chart.xAt(i)"
            y="214"
            text-anchor="middle"
          >{{ item.label }}</text>
        </g>
      </svg>
    </section>

    <section class="grid2">
      <div class="panel card" v-reveal="180">
        <div class="panel-head">
          <div>
            <h3>驿站工作量</h3>
            <p>在库、超期与格口占用</p>
          </div>
        </div>

        <div class="station-list">
          <div v-for="st in workload" :key="st.station_id" class="station-row">
            <div class="station-top">
              <div>
                <strong>{{ st.name }}</strong>
                <span class="station-code">{{ st.code }}</span>
              </div>
              <span class="station-count tabular">{{ st.used }} / {{ st.capacity }} 格</span>
            </div>
            <div class="bar">
              <span :class="level(st.occupancy)" :style="{ width: pct(st.occupancy) }"></span>
            </div>
            <div class="station-bottom">
              <span>在库 {{ st.in_stock }}</span>
              <span :class="{ warn: st.overdue > 0 }">超期 {{ st.overdue }}</span>
              <span>已取 {{ st.picked }}</span>
              <span class="occ">{{ pct(st.occupancy) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel card" v-reveal="220">
        <div class="panel-head">
          <div>
            <h3>超期分布</h3>
            <p>超期率 {{ pct(overdue.overdue_rate) }}</p>
          </div>
          <span class="panel-meta">{{ overdue.overdue }} 件超期</span>
        </div>

        <div class="buckets">
          <div v-for="b in overdue.buckets" :key="b.label" class="bucket">
            <div class="bucket-bar">
              <span :style="{ height: bucketHeight(b.count) }"></span>
            </div>
            <strong class="tabular">{{ b.count }}</strong>
            <span class="bucket-label">{{ b.label }}</span>
          </div>
        </div>

        <div class="overdue-list">
          <div v-for="item in overdue.items.slice(0, 4)" :key="item.id" class="overdue-row">
            <div>
              <strong class="mono">{{ item.tracking_no }}</strong>
              <span>{{ item.recipient_name || '未匹配' }} · {{ item.station_name }}</span>
            </div>
            <span class="overdue-days tabular">{{ item.overdue_days }} 天</span>
          </div>
          <p v-if="!overdue.items.length" class="no-overdue">暂无超期包裹，收件很顺畅。</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  Refresh, Box, Warning, Clock, CircleCheck, Van, Grid
} from '@element-plus/icons-vue'
import { overdueStats, packageTrend, stationWorkload, statsOverview } from '../api/stats'

const days = ref(7)
const loading = ref(false)

const overview = reactive({
  in_stock: 0, overdue: 0, today_inbound: 0, today_picked: 0,
  shipments_pending: 0, occupancy: 0, packages_total: 0, overdue_rate: 0, used: 0, capacity: 0
})
const trend = reactive({ days: 7, items: [], inbound_total: 0, picked_total: 0 })
const workload = ref([])
const overdue = reactive({ overdue: 0, in_stock: 0, overdue_rate: 0, buckets: [], items: [] })

const kpis = computed(() => [
  { label: '在库包裹', value: overview.in_stock, hint: '待取件', icon: Box, tint: 'rgba(0,122,255,.12)', color: '#007aff' },
  { label: '超期包裹', value: overview.overdue, hint: `超期率 ${pct(overview.overdue_rate)}`, icon: Warning, tint: 'rgba(255,149,0,.14)', color: '#c26a00' },
  { label: '今日入库', value: overview.today_inbound, hint: '登记件数', icon: Clock, tint: 'rgba(52,199,89,.13)', color: '#248a3d' },
  { label: '今日出库', value: overview.today_picked, hint: '核验取件', icon: CircleCheck, tint: 'rgba(175,82,222,.12)', color: '#8944ab' },
  { label: '待揽收寄件', value: overview.shipments_pending, hint: '等待交寄', icon: Van, tint: 'rgba(48,176,199,.14)', color: '#0b6b7d' },
  { label: '格口占用', value: pct(overview.occupancy), hint: `${overview.used} / ${overview.capacity} 格`, icon: Grid, tint: 'rgba(255,45,85,.1)', color: '#c9184a' }
])

function pct(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`
}

function level(value) {
  if (value >= 0.9) return 'high'
  if (value >= 0.6) return 'mid'
  return 'low'
}

function bucketHeight(count) {
  const max = Math.max(1, ...overdue.buckets.map((b) => b.count))
  return `${Math.max(6, (count / max) * 96)}px`
}

const chart = computed(() => {
  const items = trend.items || []
  const W = 720
  const padL = 34
  const padR = 16
  const padT = 16
  const padB = 34
  const height = 220 - padT - padB
  const max = Math.max(4, ...items.map((i) => Math.max(i.inbound, i.picked)))
  const stepX = items.length > 1 ? (W - padL - padR) / (items.length - 1) : 0

  const xAt = (i) => padL + i * stepX
  const yAt = (v) => padT + height * (1 - v / max)

  const points = (key) => items.map((item, i) => [xAt(i), yAt(item[key])])
  const line = (pts) =>
    pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ')

  const inboundPoints = points('inbound')
  const pickedPoints = points('picked')
  const areaInbound = inboundPoints.length
    ? `${line(inboundPoints)} L${xAt(items.length - 1).toFixed(1)} ${padT + height} L${padL} ${padT + height} Z`
    : ''

  return {
    xAt,
    inboundPoints,
    pickedPoints,
    lineInbound: line(inboundPoints),
    linePicked: line(pickedPoints),
    areaInbound
  }
})

const gridLines = computed(() => {
  const items = trend.items || []
  const max = Math.max(4, ...items.map((i) => Math.max(i.inbound, i.picked)))
  const height = 220 - 16 - 34
  return [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    y: 16 + height * (1 - ratio),
    label: Math.round(max * ratio)
  }))
})

async function load() {
  loading.value = true
  try {
    const [ov, tr, wl, od] = await Promise.all([
      statsOverview(),
      packageTrend({ days: days.value }),
      stationWorkload(),
      overdueStats()
    ])
    Object.assign(overview, ov)
    Object.assign(trend, tr)
    workload.value = wl.items
    Object.assign(overdue, od)
  } finally {
    loading.value = false
  }
}

function switchDays(value) {
  days.value = value
  load()
}

onMounted(load)
</script>

<style scoped>
.head-actions {
  display: flex;
  align-items: center;
  gap: 10px;
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
  padding: 6px 13px;
  font-family: inherit;
  font-size: 12px;
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

.kpis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.kpi {
  padding: 16px 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  transition: transform 0.28s var(--spring), box-shadow 0.3s var(--ease);
}

.kpi:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kpi-label {
  font-size: 11.5px;
  color: var(--label-3);
}

.kpi-icon {
  width: 28px;
  height: 28px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-value {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin-top: 4px;
}

.kpi-hint {
  font-size: 10.5px;
  color: var(--label-4);
}

.panel {
  padding: 22px 24px 16px;
  margin-bottom: 14px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.panel-head h3 {
  margin: 0 0 3px;
  font-size: 15px;
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
  background: var(--fill-2);
  padding: 4px 10px;
  border-radius: 999px;
}

.legend {
  display: flex;
  gap: 14px;
  font-size: 11.5px;
  color: var(--label-2);
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.inbound {
  background: #007aff;
}

.dot.picked {
  background: #34c759;
}

.chart {
  width: 100%;
  height: auto;
  display: block;
  overflow: visible;
}

.grid line {
  stroke: rgba(60, 60, 67, 0.08);
  stroke-width: 1;
}

.grid text {
  font-size: 9.5px;
  fill: var(--label-4);
}

.axis text {
  font-size: 9.5px;
  fill: var(--label-3);
}

.line {
  fill: none;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.line.inbound {
  stroke: #007aff;
}

.line.picked {
  stroke: #34c759;
}

.point.inbound {
  fill: #fff;
  stroke: #007aff;
  stroke-width: 2;
}

.point.picked {
  fill: #fff;
  stroke: #34c759;
  stroke-width: 2;
}

.grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.grid2 .panel {
  margin-bottom: 0;
}

.station-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-bottom: 6px;
}

.station-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 7px;
}

.station-top strong {
  font-size: 12.8px;
  font-weight: 600;
}

.station-code {
  margin-left: 7px;
  font-size: 10.5px;
  color: var(--label-4);
}

.station-count {
  font-size: 11px;
  color: var(--label-3);
}

.bar {
  height: 7px;
  border-radius: 999px;
  background: var(--fill-1);
  overflow: hidden;
}

.bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--ios-blue);
  transition: width 0.8s var(--ease-out);
}

.bar span.mid {
  background: var(--ios-orange);
}

.bar span.high {
  background: var(--ios-red);
}

.station-bottom {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 10.8px;
  color: var(--label-3);
}

.station-bottom .warn {
  color: #a85900;
}

.station-bottom .occ {
  margin-left: auto;
  color: var(--label-2);
  font-variant-numeric: tabular-nums;
}

.buckets {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: 10px;
  height: 150px;
  padding: 8px 0 4px;
  border-bottom: 1px solid var(--separator);
}

.bucket {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.bucket-bar {
  width: 100%;
  max-width: 46px;
  height: 96px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.bucket-bar span {
  width: 100%;
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(255, 149, 0, 0.85), rgba(255, 149, 0, 0.35));
  transition: height 0.7s var(--ease-out);
}

.bucket strong {
  font-size: 13px;
}

.bucket-label {
  font-size: 10.5px;
  color: var(--label-3);
}

.overdue-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
}

.overdue-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid var(--separator);
}

.overdue-row:last-child {
  border-bottom: none;
}

.overdue-row div {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.overdue-row strong {
  font-size: 12px;
}

.overdue-row span {
  font-size: 10.8px;
  color: var(--label-3);
}

.overdue-days {
  color: #a85900 !important;
  background: rgba(255, 149, 0, 0.12);
  padding: 3px 9px;
  border-radius: 999px;
  flex-shrink: 0;
}

.no-overdue {
  margin: 16px 0;
  text-align: center;
  font-size: 12px;
  color: var(--label-3);
}

.mono {
  font-family: 'SF Mono', Consolas, monospace;
}

@media (max-width: 1080px) {
  .kpis {
    grid-template-columns: repeat(2, 1fr);
  }

  .grid2 {
    grid-template-columns: 1fr;
  }
}
</style>
