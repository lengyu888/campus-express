<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>取件核验</h1>
        <p>取件码 + 手机号后四位双重校验，出库后自动释放格口</p>
      </div>
      <div class="head-actions">
        <el-button round :icon="Refresh" @click="loadRecords">刷新记录</el-button>
        <el-button round :icon="Box" @click="router.push('/packages')">包裹管理</el-button>
      </div>
    </header>

    <section class="layout">
      <article class="verify card" v-reveal>
        <div class="verify-head">
          <span class="eyebrow">
            {{ manual ? '人工核验' : '取件码核验' }}
            <i class="dot"></i>
          </span>
          <span class="step-pill">{{ step }} / 3</span>
        </div>

        <!-- 步骤一：输入取件码 -->
        <template v-if="step === 1">
          <h2>输入取件码</h2>
          <p class="lede">请向取件人索取 6 位取件码，或让其在「我的包裹」中出示。</p>

          <div class="code-field" :class="{ shake: shaking, filled: code.length === 6 }">
            <input
              ref="codeInput"
              v-model="code"
              class="code-input tabular"
              inputmode="numeric"
              maxlength="6"
              placeholder="000000"
              aria-label="取件码"
              @input="onCodeInput"
              @keyup.enter="lookup"
            />
            <span class="code-hint">{{ code.length }} / 6</span>
          </div>

          <el-button
            type="primary"
            round
            size="large"
            class="wide"
            :loading="looking"
            :disabled="code.length !== 6"
            @click="lookup"
          >
            查询包裹
          </el-button>

          <div class="divider"><span>或</span></div>
          <button v-if="!manualTrack" class="text-link" type="button" @click="manualTrack = true">
            取件码失效 / 无法提供，改用运单号核验
          </button>
          <div v-else class="manual-track">
            <el-input
              v-model="trackingInput"
              class="track-input"
              placeholder="输入或扫描运单号"
              maxlength="40"
              @keyup.enter="lookupTracking"
            />
            <el-button round :loading="looking" @click="lookupTracking">查询</el-button>
          </div>
        </template>

        <!-- 步骤二：确认包裹与手机号 -->
        <template v-else-if="step === 2 && pkg">
          <h2>{{ manual ? '人工核验出库' : '确认包裹信息' }}</h2>
          <p class="lede">
            {{ manual ? '请核对取件人身份并填写手机号后四位。' : '核对收件人信息后，输入手机号后四位完成出库。' }}
          </p>

          <div class="pkg-card">
            <div class="pkg-top">
              <div>
                <strong class="mono">{{ pkg.tracking_no }}</strong>
                <span class="pkg-sub">{{ pkg.courier_company }} · {{ typeLabel(pkg.package_type) }}</span>
              </div>
              <span class="pill" :class="`st-${pkg.status}`">{{ pkg.status_label }}</span>
            </div>
            <div class="pkg-grid">
              <div><span>收件人</span><strong>{{ pkg.recipient_name || '未匹配账号' }}</strong></div>
              <div><span>手机号</span><strong class="tabular">{{ pkg.recipient_phone }}</strong></div>
              <div><span>驿站</span><strong>{{ pkg.station_name }}</strong></div>
              <div><span>格口</span><strong>{{ pkg.shelf_code || '—' }}</strong></div>
            </div>
            <div v-if="pkg.status === 'overdue'" class="pkg-warn">
              <el-icon :size="14"><Warning /></el-icon>
              已超期 {{ pkg.overdue_days }} 天，出库时将记录超期
            </div>
            <div v-if="!manual && pkg.pickup_code" class="pkg-code">
              取件码 <strong class="tabular">{{ pkg.pickup_code }}</strong>
            </div>
          </div>

          <label class="field-label">手机号后四位</label>
          <div class="suffix-field" :class="{ shake: shaking }">
            <input
              ref="suffixInput"
              v-model="suffix"
              class="suffix-input tabular"
              inputmode="numeric"
              maxlength="4"
              placeholder="0000"
              aria-label="手机号后四位"
              @input="onSuffixInput"
              @keyup.enter="verify"
            />
            <span class="suffix-hint">与运单收件人一致</span>
          </div>

          <div v-if="manual" class="manual-box">
            <label class="field-label">人工核验说明</label>
            <el-input
              v-model="remark"
              type="textarea"
              :rows="2"
              maxlength="100"
              placeholder="如：取件码过期，已核对学生证"
            />
          </div>

          <el-button
            type="primary"
            round
            size="large"
            class="wide"
            :loading="verifying"
            :disabled="suffix.length !== 4"
            @click="verify"
          >
            确认出库
          </el-button>

          <button class="text-link back" type="button" @click="reset">
            返回，重新输入取件码
          </button>
        </template>

        <!-- 步骤三：出库成功 -->
        <template v-else-if="step === 3">
          <div class="success">
            <div class="success-mark">
              <span class="ring-a"></span>
              <span class="ring-b"></span>
              <el-icon :size="30"><Check /></el-icon>
            </div>
            <h2>出库成功</h2>
            <p class="lede">
              {{ pkg?.recipient_name || '收件人' }} 已取走包裹，格口
              {{ pickedShelf || '—' }} 已释放。
            </p>

            <dl class="success-grid">
              <div><dt>运单号</dt><dd class="mono">{{ pkg?.tracking_no }}</dd></div>
              <div><dt>核验方式</dt><dd>{{ record?.verify_label }}</dd></div>
              <div><dt>出库时间</dt><dd class="mono">{{ fmt(record?.picked_at) }}</dd></div>
              <div><dt>操作员</dt><dd>{{ record?.operator_name }}</dd></div>
            </dl>

            <el-button type="primary" round size="large" class="wide" @click="reset">
              继续核验下一件
            </el-button>
          </div>
        </template>
      </article>

      <aside class="side">
        <article class="records card" v-reveal="90">
          <div class="panel-head">
            <div>
              <h3>今日取件</h3>
              <p>最近出库记录</p>
            </div>
            <strong class="count tabular">{{ todayCount }}</strong>
          </div>

          <div v-if="!records.length" class="empty">
            <div class="empty-icon"><el-icon :size="22"><Tickets /></el-icon></div>
            <p>今天还没有取件记录</p>
          </div>

          <ul v-else class="record-list">
            <li v-for="(item, i) in records" :key="item.id" :style="{ '--i': i }">
              <span class="rec-avatar">{{ (item.recipient_name || '?').slice(-2) }}</span>
              <div class="rec-body">
                <strong>{{ item.recipient_name || '未匹配' }}</strong>
                <span class="mono">{{ item.tracking_no }}</span>
              </div>
              <div class="rec-meta">
                <span>{{ fmtTime(item.picked_at) }}</span>
                <span class="rec-verify">{{ item.verify_label }}</span>
              </div>
            </li>
          </ul>
        </article>

        <article class="tips card" v-reveal="150">
          <h3>核验要点</h3>
          <ol>
            <li>取件码仅在所属驿站有效，出库后立即失效。</li>
            <li>手机号后四位必须与运单收件人一致。</li>
            <li>超期件出库会记录超期天数，用于统计。</li>
            <li>取件码超过 7 天失效，改用人工核验。</li>
          </ol>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Box, Check, Warning, Tickets } from '@element-plus/icons-vue'
import { getPackage, getPackageByCode, listPickupRecords, pickupPackage, trackPackage } from '../api/packages'

const route = useRoute()
const router = useRouter()

const code = ref('')
const suffix = ref('')
const remark = ref('')
const pkg = ref(null)
const step = ref(1)
const manual = ref(false)
const manualTrack = ref(false)
const trackingInput = ref('')
const looking = ref(false)
const verifying = ref(false)
const picking = ref(false)
const shaking = ref(false)
const record = ref(null)
const pickedShelf = ref('')
const records = ref([])
const todayCount = ref(0)

const codeInput = ref(null)
const suffixInput = ref(null)

const types = {
  normal: '普通件',
  fragile: '易碎品',
  large: '大件',
  doc: '文件'
}

function typeLabel(value) {
  return types[value] || value
}

function fmt(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function fmtTime(value) {
  if (!value) return ''
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function onCodeInput() {
  code.value = code.value.replace(/\D/g, '').slice(0, 6)
}

function onSuffixInput() {
  suffix.value = suffix.value.replace(/\D/g, '').slice(0, 4)
}

function shake() {
  shaking.value = true
  window.setTimeout(() => (shaking.value = false), 600)
}

async function lookup() {
  if (code.value.length !== 6) return
  looking.value = true
  try {
    const data = await getPackageByCode(code.value)
    pkg.value = data
    manual.value = false
    step.value = 2
    suffix.value = ''
    await nextTick()
    suffixInput.value?.focus()
  } catch (e) {
    shake()
  } finally {
    looking.value = false
  }
}

async function verify() {
  if (suffix.value.length !== 4) {
    shake()
    return
  }
  if (manual.value && remark.value.trim().length < 2) {
    ElMessage.warning('人工核验需填写说明')
    return
  }
  verifying.value = true
  try {
    const data = await pickupPackage(pkg.value.id, {
      phone_suffix: suffix.value,
      pickup_code: manual.value ? undefined : code.value,
      verify_type: manual.value ? 'manual' : 'code_phone',
      remark: manual.value ? remark.value.trim() : undefined
    })
    pickedShelf.value = pkg.value.shelf_code
    record.value = data.record
    step.value = 3
    loadRecords()
  } catch (e) {
    shake()
  } finally {
    verifying.value = false
  }
}

async function lookupTracking() {
  const no = trackingInput.value.trim().toUpperCase()
  if (no.length < 6) {
    ElMessage.warning('请输入完整运单号')
    return
  }
  looking.value = true
  try {
    const data = await trackPackage(no)
    if (data.status !== 'in_stock' && data.status !== 'overdue') {
      ElMessage.warning(`该包裹当前为${data.status_label}状态，不能出库`)
      return
    }
    pkg.value = data
    manual.value = true
    suffix.value = ''
    remark.value = ''
    step.value = 2
    await nextTick()
    suffixInput.value?.focus()
  } catch (e) {
    shake()
  } finally {
    looking.value = false
  }
}

function reset() {
  code.value = ''
  suffix.value = ''
  remark.value = ''
  pkg.value = null
  record.value = null
  pickedShelf.value = ''
  manual.value = false
  manualTrack.value = false
  trackingInput.value = ''
  step.value = 1
  router.replace('/pickup')
  nextTick(() => codeInput.value?.focus())
}

async function loadRecords() {
  try {
    const data = await listPickupRecords({ today_only: true, page: 1, page_size: 6 })
    records.value = data.items
    todayCount.value = data.total
  } catch (e) {
    records.value = []
  }
}

async function loadFromQuery() {
  const id = route.query.id
  if (!id) return
  picking.value = true
  try {
    const data = await getPackage(Number(id))
    if (data.status !== 'in_stock' && data.status !== 'overdue') {
      ElMessage.warning(`该包裹当前为${data.status_label}状态，不能出库`)
      return
    }
    pkg.value = data
    manual.value = true
    step.value = 2
    await nextTick()
    suffixInput.value?.focus()
  } finally {
    picking.value = false
  }
}


onMounted(async () => {
  await Promise.all([loadRecords(), loadFromQuery()])
  if (step.value === 1) nextTick(() => codeInput.value?.focus())
})
</script>

<style scoped>
.head-actions {
  display: flex;
  gap: 8px;
}

.layout {
  display: grid;
  grid-template-columns: 1.12fr 0.88fr;
  gap: 14px;
  align-items: start;
}

.verify {
  padding: 30px 32px 34px;
  min-height: 520px;
  display: flex;
  flex-direction: column;
}

.verify-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--ios-blue);
  background: rgba(0, 122, 255, 0.08);
  padding: 5px 11px;
  border-radius: 999px;
}

.eyebrow .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--ios-blue);
  animation: pulse 1.8s var(--ease) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.8); }
}

.step-pill {
  font-size: 11px;
  color: var(--label-3);
  background: var(--fill-2);
  padding: 4px 10px;
  border-radius: 999px;
}

.verify h2 {
  margin: 6px 0 6px;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.lede {
  margin: 0 0 22px;
  font-size: 12.5px;
  color: var(--label-3);
  line-height: 1.6;
}

.code-field {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  background: var(--fill-2);
  border: 1px solid transparent;
  padding: 10px 0;
  margin-bottom: 18px;
  transition: background 0.25s var(--ease), box-shadow 0.25s var(--ease), border-color 0.25s;
}

.code-field:focus-within {
  background: #fff;
  border-color: rgba(0, 122, 255, 0.4);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.12);
}

.code-field.filled {
  background: rgba(0, 122, 255, 0.06);
}

.code-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  text-align: center;
  font-family: 'SF Mono', 'JetBrains Mono', Consolas, monospace;
  font-size: 44px;
  font-weight: 700;
  letter-spacing: 0.32em;
  text-indent: 0.32em;
  color: var(--label);
}

.code-input::placeholder {
  color: rgba(120, 120, 128, 0.28);
  letter-spacing: 0.28em;
}

.code-hint {
  position: absolute;
  right: 16px;
  bottom: 10px;
  font-size: 10.5px;
  color: var(--label-4);
  font-variant-numeric: tabular-nums;
}

.wide {
  width: 100%;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
}

.divider {
  position: relative;
  text-align: center;
  margin: 20px 0 14px;
  color: var(--label-4);
  font-size: 11px;
}

.divider::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  background: var(--separator);
}

.divider span {
  position: relative;
  background: #fff;
  padding: 0 10px;
}

.text-link {
  border: none;
  background: transparent;
  color: var(--ios-blue);
  font-family: inherit;
  font-size: 12px;
  cursor: pointer;
  padding: 6px;
  align-self: center;
  transition: opacity 0.2s;
}

.text-link:hover {
  opacity: 0.7;
}

.text-link.back {
  margin-top: 14px;
  color: var(--label-3);
}

.manual-track {
  display: flex;
  gap: 8px;
}

.track-input :deep(.el-input__inner) {
  font-family: 'SF Mono', Consolas, monospace;
  letter-spacing: 0.06em;
}

/* 包裹预览 */
.pkg-card {
  border-radius: 18px;
  background: var(--fill-2);
  padding: 16px 18px;
  margin-bottom: 20px;
  animation: card-in 0.45s var(--ease-out) both;
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
}

.pkg-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.pkg-top strong {
  display: block;
  font-size: 15px;
  letter-spacing: -0.01em;
}

.pkg-sub {
  font-size: 11.5px;
  color: var(--label-3);
}

.pkg-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 16px;
}

.pkg-grid span {
  display: block;
  font-size: 10.5px;
  color: var(--label-3);
  margin-bottom: 2px;
}

.pkg-grid strong {
  font-size: 12.5px;
  font-weight: 550;
}

.pkg-warn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255, 149, 0, 0.12);
  color: #a85900;
  font-size: 11.5px;
}

.pkg-code {
  margin-top: 12px;
  font-size: 12px;
  color: var(--label-3);
}

.pkg-code strong {
  margin-left: 8px;
  font-size: 18px;
  letter-spacing: 0.16em;
  color: #0a5bb5;
}

.field-label {
  display: block;
  font-size: 11.5px;
  color: var(--label-3);
  margin-bottom: 7px;
}

.suffix-field {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 16px;
  border-radius: 16px;
  background: var(--fill-2);
  border: 1px solid transparent;
  margin-bottom: 18px;
  transition: background 0.25s var(--ease), box-shadow 0.25s var(--ease), border-color 0.25s;
}

.suffix-field:focus-within {
  background: #fff;
  border-color: rgba(0, 122, 255, 0.4);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.12);
}

.suffix-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.4em;
  padding: 6px 0;
}

.suffix-input::placeholder {
  color: rgba(120, 120, 128, 0.3);
}

.suffix-hint {
  font-size: 10.5px;
  color: var(--label-4);
  flex-shrink: 0;
}

.manual-box {
  margin-bottom: 16px;
}

/* 成功态 */
.success {
  text-align: center;
  padding: 22px 0 8px;
  animation: success-in 0.5s var(--ease-out) both;
}

@keyframes success-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
}

.success-mark {
  position: relative;
  width: 76px;
  height: 76px;
  margin: 0 auto 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(160deg, #4ade80, #34c759);
  box-shadow: 0 12px 30px rgba(52, 199, 89, 0.35);
  animation: pop 0.55s var(--spring) both;
}

@keyframes pop {
  from { transform: scale(0.45); }
}

.success-mark .ring-a,
.success-mark .ring-b {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 1px solid rgba(52, 199, 89, 0.4);
  animation: ripple 1.6s var(--ease-out) infinite;
}

.success-mark .ring-b {
  animation-delay: 0.5s;
}

@keyframes ripple {
  0% { transform: scale(0.95); opacity: 0.8; }
  100% { transform: scale(1.5); opacity: 0; }
}

.success-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 18px;
  text-align: left;
  background: var(--fill-2);
  border-radius: 16px;
  padding: 16px 18px;
  margin: 18px 0 22px;
}

.success-grid dt {
  font-size: 10.5px;
  color: var(--label-3);
  margin-bottom: 2px;
}

.success-grid dd {
  margin: 0;
  font-size: 12.5px;
}

/* 侧栏 */
.side {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.records {
  padding: 22px 22px 16px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.panel-head h3 {
  margin: 0 0 2px;
  font-size: 14.5px;
  font-weight: 650;
}

.panel-head p {
  margin: 0;
  font-size: 11.5px;
  color: var(--label-3);
}

.count {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--ios-blue);
}

.record-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.record-list li {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 0;
  border-bottom: 1px solid var(--separator);
  animation: rec-in 0.4s var(--ease-out) both;
  animation-delay: calc(var(--i) * 45ms);
}

.record-list li:last-child {
  border-bottom: none;
}

@keyframes rec-in {
  from {
    opacity: 0;
    transform: translateX(10px);
  }
}

.rec-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #1d7a37;
  background: rgba(52, 199, 89, 0.14);
}

.rec-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.rec-body strong {
  font-size: 12.5px;
}

.rec-body span {
  font-size: 10.5px;
  color: var(--label-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rec-meta {
  margin-left: auto;
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}

.rec-meta span:first-child {
  font-size: 11.5px;
  color: var(--label-2);
  font-variant-numeric: tabular-nums;
}

.rec-verify {
  font-size: 10px;
  color: var(--label-4);
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 34px 0 38px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 122, 255, 0.08);
  color: var(--ios-blue);
}

.empty p {
  margin: 0;
  font-size: 12px;
  color: var(--label-3);
}

.tips {
  padding: 20px 22px 22px;
}

.tips h3 {
  margin: 0 0 12px;
  font-size: 13.5px;
}

.tips ol {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.tips li {
  font-size: 11.8px;
  color: var(--label-2);
  line-height: 1.55;
}

.pill {
  display: inline-flex;
  align-items: center;
  height: 21px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
  flex-shrink: 0;
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

.shake {
  animation: shake 0.55s cubic-bezier(0.36, 0.07, 0.19, 0.97);
}

@keyframes shake {
  10%, 90% { transform: translateX(-2px); }
  20%, 80% { transform: translateX(4px); }
  30%, 50%, 70% { transform: translateX(-7px); }
  40%, 60% { transform: translateX(7px); }
}

.mono {
  font-family: 'SF Mono', 'JetBrains Mono', Consolas, monospace;
}

@media (max-width: 1080px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .verify {
    min-height: auto;
  }
}
</style>
