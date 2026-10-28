<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>包裹管理</h1>
        <p>
          {{ summary.in_stock }} 件在库 · {{ summary.overdue }} 件超期 · 今日入库
          {{ summary.today_inbound }} 件
        </p>
      </div>
      <div class="head-actions">
        <el-button round :icon="Refresh" :loading="loading" @click="reload">刷新</el-button>
        <el-button round :icon="Files" @click="openBatch">批量入库</el-button>
        <el-button type="primary" round :icon="Plus" @click="openInbound">入库登记</el-button>
      </div>
    </header>

    <section class="stats">
      <article
        v-for="(item, i) in statCards"
        :key="item.label"
        class="stat card"
        v-reveal="i * 60"
      >
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
      <div class="seg" role="group" aria-label="包裹状态筛选">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          :class="{ active: status === tab.value }"
          @click="switchStatus(tab.value)"
        >
          {{ tab.label }}
          <span class="seg-count">{{ tab.count }}</span>
        </button>
      </div>
      <div class="toolbar-right">
        <el-select
          v-if="isAdmin"
          v-model="stationId"
          clearable
          placeholder="全部驿站"
          class="station-select"
          @change="reload"
        >
          <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-input
          v-model="keyword"
          class="search"
          placeholder="运单号 / 姓名 / 手机号 / 取件码"
          clearable
          :prefix-icon="Search"
          @keyup.enter="reload"
          @clear="reload"
        />
      </div>
    </section>

    <section class="table-card card" v-reveal="140">
      <div v-if="loading && !rows.length" class="skeleton" aria-label="加载中">
        <div v-for="i in 6" :key="i" class="sk-row" :style="{ '--i': i }">
          <span class="sk-avatar"></span>
          <span class="sk-main"></span>
          <span class="sk-sub"></span>
          <span class="sk-pill"></span>
        </div>
      </div>

      <el-table
        v-else
        :data="rows"
        class="pkg-table"
        @row-click="openDetail"
      >
        <el-table-column label="运单号" min-width="180">
          <template #default="{ row }">
            <div class="cell-main mono">{{ row.tracking_no }}</div>
            <div class="cell-sub">{{ row.courier_company }} · {{ typeLabel(row.package_type) }}</div>
          </template>
        </el-table-column>

        <el-table-column label="收件人" min-width="150">
          <template #default="{ row }">
            <div class="cell-main">{{ row.recipient_name || '未匹配账号' }}</div>
            <div class="cell-sub tabular">{{ row.recipient_phone }}</div>
          </template>
        </el-table-column>

        <el-table-column label="位置" min-width="150">
          <template #default="{ row }">
            <div class="cell-main">{{ row.station_name }}</div>
            <div class="cell-sub">
              {{ row.shelf_code ? `${row.shelf_code} 货架` : '格口已释放' }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="104">
          <template #default="{ row }">
            <span class="pill" :class="`st-${row.status}`">{{ row.status_label }}</span>
          </template>
        </el-table-column>

        <el-table-column label="取件码" width="110">
          <template #default="{ row }">
            <span v-if="row.pickup_code" class="code-badge tabular">{{ row.pickup_code }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="入库时间" width="150">
          <template #default="{ row }">
            <span class="mono small">{{ fmt(row.stored_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="132" align="right">
          <template #default="{ row }">
            <div class="row-actions" @click.stop>
              <button v-if="inStock(row)" class="mini primary" type="button" @click="goPickup(row)">
                核验
              </button>
              <el-dropdown trigger="click" @command="(cmd) => onCommand(cmd, row)">
                <button class="mini" type="button" aria-label="更多操作">更多</button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="detail">查看详情</el-dropdown-item>
                    <el-dropdown-item v-if="inStock(row)" command="shelf">调整格口</el-dropdown-item>
                    <el-dropdown-item v-if="inStock(row)" command="return">登记退回</el-dropdown-item>
                    <el-dropdown-item v-if="inStock(row)" command="exception" divided>
                      登记异常
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !rows.length" class="empty">
        <div class="empty-icon"><el-icon :size="26"><Box /></el-icon></div>
        <h3>没有符合条件的包裹</h3>
        <p>换个筛选条件，或登记一件新的入库包裹。</p>
        <el-button type="primary" round :icon="Plus" @click="openInbound">入库登记</el-button>
      </div>

      <div v-if="total > 0" class="table-foot">
        <span class="foot-total">共 {{ total }} 件</span>
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

    <!-- 入库抽屉 -->
    <el-drawer v-model="inboundVisible" :with-header="false" size="520px" @closed="resetInbound">
      <div class="drawer-head">
        <div>
          <h3>入库登记</h3>
          <span>扫描或输入运单号，系统自动分配格口并生成取件码</span>
        </div>
        <button class="drawer-close" type="button" aria-label="关闭" @click="inboundVisible = false">
          <el-icon :size="16"><Close /></el-icon>
        </button>
      </div>

      <div v-if="inboundResult" class="result">
        <div class="result-check"><el-icon :size="26"><Check /></el-icon></div>
        <h4>入库成功</h4>
        <p class="result-sub">{{ inboundResult.tracking_no }} · {{ inboundResult.station_name }}</p>

        <div class="code-card">
          <span>取件码</span>
          <strong class="tabular">{{ inboundResult.pickup_code }}</strong>
          <button type="button" @click="copyCode(inboundResult.pickup_code)">
            <el-icon :size="14"><CopyDocument /></el-icon>
            复制
          </button>
        </div>

        <div class="result-meta">
          <span>{{ inboundResult.shelf_code }} 货架</span>
          <span>{{ inboundResult.recipient_name || '未匹配账号' }} {{ inboundResult.recipient_phone }}</span>
        </div>

        <div class="result-actions">
          <el-button round @click="resetInbound">继续入库</el-button>
          <el-button type="primary" round @click="viewResult">查看包裹</el-button>
        </div>
      </div>

      <el-form
        v-else
        ref="inboundRef"
        :model="form"
        :rules="rules"
        label-position="top"
        class="inbound-form"
      >
        <el-form-item label="入库驿站" prop="station_id">
          <el-select v-model="form.station_id" placeholder="选择驿站" style="width: 100%" @change="loadInboundShelves">
            <el-option
              v-for="s in stations"
              :key="s.id"
              :label="`${s.name}（剩余 ${s.capacity - s.used_count} 格）`"
              :value="s.id"
              :disabled="s.status === 0"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="运单号" prop="tracking_no">
          <el-input
            v-model="form.tracking_no"
            class="mono-input"
            placeholder="扫描枪扫描或手动输入"
            maxlength="40"
            clearable
          />
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="收件人手机号" prop="recipient_phone">
            <el-input v-model="form.recipient_phone" maxlength="11" placeholder="11 位手机号" />
          </el-form-item>
          <el-form-item label="收件人姓名">
            <el-input v-model="form.recipient_name" maxlength="50" placeholder="选填，自动匹配" />
          </el-form-item>
        </div>

        <div class="form-grid">
          <el-form-item label="快递公司" prop="courier_company">
            <el-select v-model="form.courier_company" style="width: 100%">
              <el-option v-for="c in couriers" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
          <el-form-item label="包裹类型">
            <el-select v-model="form.package_type" style="width: 100%">
              <el-option v-for="t in types" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
          </el-form-item>
        </div>

        <div class="form-grid">
          <el-form-item label="重量（kg）">
            <el-input-number v-model="form.weight" :min="0" :max="999" :precision="2" :step="0.1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="指定货架">
            <el-select v-model="form.shelf_id" clearable placeholder="自动分配" style="width: 100%">
              <el-option
                v-for="sh in inboundShelves"
                :key="sh.id"
                :label="`${sh.code}（剩余 ${sh.capacity - sh.used_count}）`"
                :value="sh.id"
                :disabled="sh.used_count >= sh.capacity || sh.status === 0"
              />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="255" show-word-limit />
        </el-form-item>

        <div class="form-tip">
          <el-icon :size="14"><InfoFilled /></el-icon>
          <span>取件码有效期 7 天，入库满 3 天自动标记超期。</span>
        </div>

        <div class="form-actions">
          <el-button round @click="inboundVisible = false">取消</el-button>
          <el-button type="primary" round :loading="submitting" @click="submitInbound">
            确认入库
          </el-button>
        </div>
      </el-form>
    </el-drawer>

    <!-- 批量入库 -->
    <el-dialog v-model="batchVisible" title="批量入库" width="560px" :close-on-click-modal="false">
      <div v-if="batchResult" class="batch-result">
        <div class="batch-summary">
          <span class="ok">成功 {{ batchResult.success }}</span>
          <span class="bad">失败 {{ batchResult.failed }}</span>
        </div>
        <div class="batch-list">
          <div v-for="item in batchResult.items" :key="item.index" class="batch-row">
            <span class="mono">{{ item.tracking_no }}</span>
            <span v-if="item.success" class="batch-code tabular">{{ item.pickup_code }}</span>
            <span v-else class="batch-err">{{ item.message }}</span>
          </div>
        </div>
      </div>

      <el-form v-else label-position="top">
        <el-form-item label="入库驿站">
          <el-select v-model="batchForm.station_id" placeholder="选择驿站" style="width: 100%">
            <el-option
              v-for="s in stations"
              :key="s.id"
              :label="`${s.name}（剩余 ${s.capacity - s.used_count} 格）`"
              :value="s.id"
              :disabled="s.status === 0"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="快递公司">
          <el-select v-model="batchForm.courier_company" style="width: 100%">
            <el-option v-for="c in couriers" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="运单清单">
          <el-input
            v-model="batchForm.text"
            type="textarea"
            :rows="7"
            placeholder="每行一条：运单号,手机号,姓名（姓名可省略）&#10;示例：SF1000000001,13800000002,张同学"
          />
        </el-form-item>
        <div class="form-tip">
          <el-icon :size="14"><InfoFilled /></el-icon>
          <span>单次最多 50 条，重复运单号会在结果中单独标记，不影响其他条目。</span>
        </div>
      </el-form>

      <template #footer>
        <template v-if="batchResult">
          <el-button round @click="resetBatch">继续批量</el-button>
          <el-button type="primary" round @click="closeBatch">完成</el-button>
        </template>
        <template v-else>
          <el-button round @click="batchVisible = false">取消</el-button>
          <el-button type="primary" round :loading="batchLoading" @click="submitBatch">开始入库</el-button>
        </template>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" :with-header="false" size="480px">
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

        <div class="detail-status" :class="`st-${detail.status}`">
          <div>
            <span class="pill" :class="`st-${detail.status}`">{{ detail.status_label }}</span>
            <strong>{{ statusHeadline(detail) }}</strong>
          </div>
          <span class="detail-days tabular">
            {{ detail.status === 'picked' ? '已出库' : `已存放 ${detail.days_in_stock} 天` }}
          </span>
        </div>

        <div v-if="detail.pickup_code" class="detail-code">
          <span>取件码</span>
          <strong class="tabular">{{ detail.pickup_code }}</strong>
          <button type="button" @click="copyCode(detail.pickup_code)">
            <el-icon :size="14"><CopyDocument /></el-icon>
          </button>
        </div>

        <dl class="detail-grid">
          <div><dt>收件人</dt><dd>{{ detail.recipient_name || '未匹配账号' }}</dd></div>
          <div><dt>手机号</dt><dd class="tabular">{{ detail.recipient_phone }}</dd></div>
          <div><dt>驿站</dt><dd>{{ detail.station_name }}</dd></div>
          <div><dt>货架</dt><dd>{{ detail.shelf_code || '格口已释放' }}</dd></div>
          <div><dt>入库时间</dt><dd class="mono small">{{ fmt(detail.stored_at) }}</dd></div>
          <div><dt>操作人</dt><dd>{{ detail.created_by_name || '—' }}</dd></div>
          <div v-if="detail.weight"><dt>重量</dt><dd>{{ detail.weight }} kg</dd></div>
          <div><dt>超期天数</dt><dd>{{ detail.overdue_days }} 天</dd></div>
        </dl>

        <div v-if="detail.remark" class="detail-remark">{{ detail.remark }}</div>

        <h4 class="timeline-title">流转记录</h4>
        <div class="timeline">
          <div v-for="(item, i) in detail.timeline" :key="i" class="tl-item" :class="item.type">
            <span class="tl-dot"></span>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.desc }}</p>
              <span class="tl-time mono">{{ fmt(item.at) }}<template v-if="item.operator"> · {{ item.operator }}</template></span>
            </div>
          </div>
        </div>

        <div v-if="inStock(detail)" class="detail-actions">
          <el-button round :icon="Position" @click="openShelfDialog(detail)">调整格口</el-button>
          <el-button round :icon="RefreshLeft" @click="openReturnDialog(detail)">登记退回</el-button>
          <el-button type="primary" round :icon="CircleCheck" @click="goPickup(detail)">去核验</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 调整格口 -->
    <el-dialog v-model="shelfDialog" title="调整格口" width="420px">
      <p class="dialog-tip">{{ activeRow?.tracking_no }} · 当前 {{ activeRow?.shelf_code || '未分配' }}</p>
      <el-select v-model="targetShelf" placeholder="选择目标货架" style="width: 100%">
        <el-option
          v-for="sh in detailShelves"
          :key="sh.id"
          :label="`${sh.code}（剩余 ${sh.capacity - sh.used_count}）`"
          :value="sh.id"
          :disabled="sh.used_count >= sh.capacity || sh.id === activeRow?.shelf_id"
        />
      </el-select>
      <template #footer>
        <el-button round @click="shelfDialog = false">取消</el-button>
        <el-button type="primary" round :loading="actionLoading" @click="submitShelf">确认调整</el-button>
      </template>
    </el-dialog>

    <!-- 登记退回 -->
    <el-dialog v-model="returnDialog" title="登记退回" width="420px">
      <p class="dialog-tip">{{ activeRow?.tracking_no }} · 退回后格口将自动释放</p>
      <el-input v-model="returnReason" type="textarea" :rows="3" maxlength="100" show-word-limit
                placeholder="退回原因，如：超期未取、收件人拒收" />
      <template #footer>
        <el-button round @click="returnDialog = false">取消</el-button>
        <el-button type="primary" round :loading="actionLoading" @click="submitReturn">确认退回</el-button>
      </template>
    </el-dialog>

    <!-- 登记异常 -->
    <el-dialog v-model="exceptionDialog" title="登记异常件" width="420px">
      <p class="dialog-tip">{{ activeRow?.tracking_no }} · 异常件将暂停出库</p>
      <el-select v-model="exceptionType" style="width: 100%; margin-bottom: 12px">
        <el-option label="包装破损" value="damaged" />
        <el-option label="包裹丢失" value="lost" />
        <el-option label="错分驿站" value="wrong_station" />
        <el-option label="异常退回" value="returned" />
        <el-option label="其他异常" value="other" />
      </el-select>
      <el-input v-model="exceptionRemark" type="textarea" :rows="3" maxlength="200" placeholder="补充说明" />
      <template #footer>
        <el-button round @click="exceptionDialog = false">取消</el-button>
        <el-button type="primary" round :loading="actionLoading" @click="submitException">确认登记</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh, Plus, Search, Box, CircleCheck, Warning, Clock, Close, Check, Files,
  CopyDocument, InfoFilled, Position, RefreshLeft
} from '@element-plus/icons-vue'
import {
  createPackage, batchCreatePackages, getPackage, listPackages,
  markPackageException, movePackageShelf, packagesSummary, returnPackage
} from '../api/packages'
import { listShelves, listStations } from '../api/stations'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const isAdmin = computed(() => auth.role === 'admin')

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)
const status = ref('')
const keyword = ref('')
const stationId = ref(null)
const stations = ref([])

const summary = reactive({
  in_stock: 0, overdue: 0, today_inbound: 0, today_picked: 0,
  picked: 0, returned: 0, exception: 0, total: 0
})

const tabs = computed(() => [
  { label: '全部', value: '', count: summary.total },
  { label: '在库', value: 'in_stock', count: summary.in_stock },
  { label: '超期', value: 'overdue', count: summary.overdue },
  { label: '已取件', value: 'picked', count: summary.picked },
  { label: '已退回', value: 'returned', count: summary.returned },
  { label: '异常', value: 'exception', count: summary.exception }
])

const statCards = computed(() => [
  { label: '在库', value: summary.in_stock, hint: '待取件包裹', icon: Box, tint: 'rgba(0,122,255,.12)', color: '#007aff' },
  { label: '超期', value: summary.overdue, hint: '超过 3 天未取', icon: Warning, tint: 'rgba(255,149,0,.14)', color: '#c26a00' },
  { label: '今日入库', value: summary.today_inbound, hint: '今日登记', icon: Clock, tint: 'rgba(52,199,89,.13)', color: '#248a3d' },
  { label: '今日出库', value: summary.today_picked, hint: '已核验取件', icon: CircleCheck, tint: 'rgba(175,82,222,.12)', color: '#8944ab' }
])

const couriers = ['顺丰速运', '京东物流', '圆通速递', '中通快递', '申通快递', '韵达快递', 'EMS', '极兔速递']
const types = [
  { label: '普通件', value: 'normal' },
  { label: '易碎品', value: 'fragile' },
  { label: '大件', value: 'large' },
  { label: '文件', value: 'doc' }
]

function typeLabel(value) {
  return types.find((t) => t.value === value)?.label || value
}

function fmt(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function inStock(row) {
  return row && (row.status === 'in_stock' || row.status === 'overdue')
}

function statusHeadline(row) {
  if (row.status === 'picked') return '已于 ' + fmt(row.picked_at) + ' 出库'
  if (row.status === 'overdue') return `已超期 ${row.overdue_days} 天，请尽快通知收件人`
  if (row.status === 'returned') return '包裹已退回发件方'
  if (row.status === 'exception') return '异常件，等待处理'
  return '在库待取，取件码已发送'
}

async function load() {
  loading.value = true
  try {
    const [data, sum] = await Promise.all([
      listPackages({ page: page.value, page_size: pageSize, status: status.value || undefined, keyword: keyword.value || undefined, station_id: stationId.value || undefined }),
      packagesSummary({ station_id: stationId.value || undefined })
    ])
    rows.value = data.items
    total.value = data.total
    Object.assign(summary, sum)
  } finally {
    loading.value = false
  }
}

async function reload() {
  page.value = 1
  await load()
}

function switchStatus(value) {
  status.value = value
  page.value = 1
  load()
}

/* 入库 */
const inboundVisible = ref(false)
const inboundRef = ref()
const inboundShelves = ref([])
const inboundResult = ref(null)
const submitting = ref(false)

const form = reactive({
  station_id: null,
  tracking_no: '',
  recipient_phone: '',
  recipient_name: '',
  courier_company: '顺丰速运',
  package_type: 'normal',
  weight: null,
  shelf_id: null,
  remark: ''
})

const rules = {
  station_id: [{ required: true, message: '请选择入库驿站', trigger: 'change' }],
  tracking_no: [
    { required: true, message: '请输入运单号', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9-]{6,40}$/, message: '运单号为 6-40 位字母、数字或短横线', trigger: 'blur' }
  ],
  recipient_phone: [
    { required: true, message: '请输入收件人手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  courier_company: [{ required: true, message: '请选择快递公司', trigger: 'change' }]
}

function openInbound() {
  inboundVisible.value = true
  if (!form.station_id && stations.value.length) {
    const mine = stations.value.find((s) => s.manager_id === auth.user?.id) || stations.value[0]
    form.station_id = mine.id
    loadInboundShelves(form.station_id)
  }
}

async function loadInboundShelves(id) {
  form.shelf_id = null
  if (!id) return
  const data = await listShelves(id)
  inboundShelves.value = data.items
}

async function submitInbound() {
  const valid = await inboundRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const data = await createPackage({ ...form, weight: form.weight ?? null })
    inboundResult.value = data
    ElMessage.success('入库成功，取件码已生成')
    await Promise.all([load(), refreshStations()])
  } finally {
    submitting.value = false
  }
}

function resetInbound() {
  inboundResult.value = null
  Object.assign(form, {
    tracking_no: '', recipient_phone: '', recipient_name: '',
    package_type: 'normal', weight: null, shelf_id: null, remark: ''
  })
  if (form.station_id) loadInboundShelves(form.station_id)
}

function viewResult() {
  inboundVisible.value = false
  openDetail(inboundResult.value)
}

function closeBatch() {
  batchVisible.value = false
  batchResult.value = null
  batchForm.text = ''
  load()
}

function copyCode(code) {
  const text = String(code)
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(
      () => ElMessage.success(`取件码 ${text} 已复制`),
      () => ElMessage.warning(text)
    )
  } else {
    ElMessage.success(`取件码 ${text}`)
  }
}

/* 批量入库 */
const batchVisible = ref(false)
const batchLoading = ref(false)
const batchResult = ref(null)
const batchForm = reactive({ station_id: null, courier_company: '顺丰速运', text: '' })

function openBatch() {
  if (!batchForm.station_id && stations.value.length) {
    const mine = stations.value.find((s) => s.manager_id === auth.user?.id) || stations.value[0]
    batchForm.station_id = mine.id
  }
  batchVisible.value = true
}

async function submitBatch() {
  const lines = batchForm.text.split('\n').map((l) => l.trim()).filter(Boolean)
  if (!batchForm.station_id || !lines.length) {
    ElMessage.warning('请选择驿站并粘贴运单清单')
    return
  }
  const items = []
  for (const line of lines) {
    const [tracking_no, recipient_phone, recipient_name] = line.split(/[,，\s]+/).filter(Boolean)
    if (!tracking_no || !recipient_phone) {
      ElMessage.error(`格式有误：${line}`)
      return
    }
    items.push({ tracking_no, recipient_phone, recipient_name, courier_company: batchForm.courier_company })
  }
  batchLoading.value = true
  try {
    batchResult.value = await batchCreatePackages({ station_id: batchForm.station_id, items })
    await load()
  } finally {
    batchLoading.value = false
  }
}

function resetBatch() {
  batchResult.value = null
  batchForm.text = ''
}

/* 详情与操作 */
const detailVisible = ref(false)
const detail = ref(null)
const activeRow = ref(null)
const actionLoading = ref(false)

const shelfDialog = ref(false)
const detailShelves = ref([])
const targetShelf = ref(null)

const returnDialog = ref(false)
const returnReason = ref('')

const exceptionDialog = ref(false)
const exceptionType = ref('damaged')
const exceptionRemark = ref('')

async function openDetail(row) {
  const data = await getPackage(row.id)
  detail.value = data
  detailVisible.value = true
}

async function onCommand(cmd, row) {
  if (cmd === 'detail') return openDetail(row)
  if (cmd === 'shelf') return openShelfDialog(row)
  if (cmd === 'return') return openReturnDialog(row)
  if (cmd === 'exception') {
    activeRow.value = row
    exceptionType.value = 'damaged'
    exceptionRemark.value = ''
    exceptionDialog.value = true
  }
}

async function openShelfDialog(row) {
  activeRow.value = row
  targetShelf.value = null
  shelfDialog.value = true
  const data = await listShelves(row.station_id)
  detailShelves.value = data.items
}

async function submitShelf() {
  if (!targetShelf.value) {
    ElMessage.warning('请选择目标货架')
    return
  }
  actionLoading.value = true
  try {
    await movePackageShelf(activeRow.value.id, targetShelf.value)
    ElMessage.success('格口已调整')
    shelfDialog.value = false
    detailVisible.value = false
    await load()
  } finally {
    actionLoading.value = false
  }
}

function openReturnDialog(row) {
  activeRow.value = row
  returnReason.value = ''
  returnDialog.value = true
}

async function submitReturn() {
  if (returnReason.value.trim().length < 2) {
    ElMessage.warning('请填写退回原因')
    return
  }
  actionLoading.value = true
  try {
    await returnPackage(activeRow.value.id, returnReason.value.trim())
    ElMessage.success('已登记退回')
    returnDialog.value = false
    detailVisible.value = false
    await load()
  } finally {
    actionLoading.value = false
  }
}

async function submitException() {
  actionLoading.value = true
  try {
    await markPackageException(activeRow.value.id, {
      exception_type: exceptionType.value,
      remark: exceptionRemark.value || undefined
    })
    ElMessage.success('异常已登记')
    exceptionDialog.value = false
    await load()
  } finally {
    actionLoading.value = false
  }
}

function goPickup(row) {
  router.push({ path: '/pickup', query: { id: row.id } })
}

async function refreshStations() {
  const data = await listStations()
  stations.value = data.items
}

onMounted(async () => {
  await refreshStations()
  await load()
})
</script>

<style scoped>
.head-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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
  gap: 14px;
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
  flex-wrap: wrap;
}

.seg button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  border-radius: 9px;
  padding: 7px 13px;
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

.seg-count {
  font-size: 10.5px;
  font-variant-numeric: tabular-nums;
  color: var(--label-4);
}

.seg button.active .seg-count {
  color: var(--ios-blue);
}

.toolbar-right {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.station-select {
  width: 150px;
}

.search {
  width: 250px;
}

.table-card {
  padding: 6px 8px 8px;
  overflow: hidden;
}

.pkg-table {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(0, 122, 255, 0.045);
  background: transparent;
}

.pkg-table :deep(th.el-table__cell) {
  background: transparent;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--label-3);
  border-bottom: 1px solid var(--separator);
  padding: 12px 0;
}

.pkg-table :deep(td.el-table__cell) {
  border-bottom: 1px solid var(--separator);
  padding: 13px 0;
}

.pkg-table :deep(.el-table__row) {
  cursor: pointer;
}

.cell-main {
  font-size: 13px;
  color: var(--label);
  font-weight: 550;
}

.cell-sub {
  margin-top: 3px;
  font-size: 11.5px;
  color: var(--label-3);
}

.mono {
  font-family: 'SF Mono', 'JetBrains Mono', Consolas, monospace;
  letter-spacing: -0.01em;
}

.small {
  font-size: 11.5px;
}

.muted {
  color: var(--label-4);
}

.pill {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 11px;
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

.code-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 9px;
  border-radius: 8px;
  background: rgba(0, 122, 255, 0.08);
  color: #0a5bb5;
  font-size: 12.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
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

.mini.primary:hover {
  background: #1a86ff;
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
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--label-3);
}

.skeleton {
  padding: 10px 14px 4px;
}

.sk-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 15px 8px;
  border-bottom: 1px solid var(--separator);
  opacity: 0;
  animation: skeleton-in 0.35s var(--ease-out) forwards;
  animation-delay: calc(var(--i) * 40ms);
}

.sk-avatar,
.sk-main,
.sk-sub,
.sk-pill {
  background: linear-gradient(90deg, rgba(120, 120, 128, 0.1) 25%, rgba(120, 120, 128, 0.16) 37%, rgba(120, 120, 128, 0.1) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
  border-radius: 8px;
}

.sk-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
}

.sk-main {
  width: 150px;
  height: 12px;
}

.sk-sub {
  width: 190px;
  height: 10px;
}

.sk-pill {
  width: 88px;
  height: 22px;
  border-radius: 999px;
  margin-left: auto;
}

@keyframes shimmer {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

@keyframes skeleton-in {
  to { opacity: 1; }
}

/* 抽屉 */
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
  transition: background 0.2s var(--ease), transform 0.2s var(--spring);
}

.drawer-close:hover {
  background: rgba(120, 120, 128, 0.16);
}

.drawer-close:active {
  transform: scale(0.92);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.inbound-form :deep(.el-form-item__label) {
  font-size: 12px;
  color: var(--label-2);
  padding-bottom: 5px;
}

.mono-input :deep(.el-input__inner) {
  font-family: 'SF Mono', Consolas, monospace;
  letter-spacing: 0.04em;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  color: var(--label-3);
  background: rgba(0, 122, 255, 0.06);
  border-radius: 12px;
  padding: 10px 12px;
  margin: 4px 0 18px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 入库结果 */
.result {
  text-align: center;
  padding-top: 12px;
  animation: result-in 0.55s var(--ease-out) both;
}

@keyframes result-in {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.98);
  }
}

.result-check {
  width: 62px;
  height: 62px;
  border-radius: 50%;
  margin: 0 auto 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(160deg, #4ade80, #34c759);
  box-shadow: 0 10px 26px rgba(52, 199, 89, 0.34);
  animation: pop 0.5s var(--spring) both;
}

@keyframes pop {
  from { transform: scale(0.4); }
}

.result h4 {
  margin: 0 0 4px;
  font-size: 17px;
}

.result-sub {
  margin: 0 0 18px;
  font-size: 12px;
  color: var(--label-3);
}

.code-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.08), rgba(94, 92, 230, 0.1));
  margin-bottom: 14px;
}

.code-card span {
  font-size: 11.5px;
  color: var(--label-3);
}

.code-card strong {
  font-size: 38px;
  letter-spacing: 0.24em;
  font-weight: 700;
  color: #0a5bb5;
  font-family: 'SF Mono', Consolas, monospace;
}

.code-card button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  color: #0a5bb5;
  font-family: inherit;
  font-size: 11.5px;
  padding: 4px 10px;
  border-radius: 999px;
  cursor: pointer;
}

.result-meta {
  display: flex;
  justify-content: center;
  gap: 14px;
  font-size: 11.5px;
  color: var(--label-3);
  margin-bottom: 22px;
  flex-wrap: wrap;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

/* 批量 */
.batch-summary {
  display: flex;
  gap: 14px;
  font-size: 13px;
  margin-bottom: 12px;
}

.batch-summary .ok {
  color: #1d7a37;
  font-weight: 600;
}

.batch-summary .bad {
  color: #b3261e;
  font-weight: 600;
}

.batch-list {
  max-height: 320px;
  overflow: auto;
  border-radius: 12px;
  background: var(--fill-2);
  padding: 6px 12px;
}

.batch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--separator);
  font-size: 12px;
}

.batch-row:last-child {
  border-bottom: none;
}

.batch-code {
  color: #0a5bb5;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.batch-err {
  color: #b3261e;
  font-size: 11.5px;
}

/* 详情 */
.detail-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--fill-2);
  margin-bottom: 14px;
}

.detail-status > div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail-status strong {
  font-size: 12.5px;
  font-weight: 550;
  color: var(--label-2);
}

.detail-days {
  font-size: 11.5px;
  color: var(--label-3);
  flex-shrink: 0;
}

.detail-code {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 16px;
  background: rgba(0, 122, 255, 0.07);
  margin-bottom: 14px;
}

.detail-code span {
  font-size: 11.5px;
  color: var(--label-3);
}

.detail-code strong {
  font-size: 24px;
  letter-spacing: 0.2em;
  color: #0a5bb5;
  font-family: 'SF Mono', Consolas, monospace;
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

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 18px;
  margin: 0 0 14px;
}

.detail-grid dt {
  font-size: 11px;
  color: var(--label-3);
  margin-bottom: 2px;
}

.detail-grid dd {
  margin: 0;
  font-size: 12.5px;
  color: var(--label);
}

.detail-remark {
  font-size: 12px;
  color: var(--label-2);
  background: rgba(255, 149, 0, 0.09);
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 14px;
}

.timeline-title {
  margin: 20px 0 12px;
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

.tl-item.returned .tl-dot {
  background: var(--label-4);
  box-shadow: none;
}

.tl-item.exception .tl-dot {
  background: var(--ios-red);
  box-shadow: 0 0 0 3px rgba(255, 59, 48, 0.12);
}

.tl-item strong {
  font-size: 12.5px;
  font-weight: 600;
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
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid var(--separator);
  flex-wrap: wrap;
}

.detail-actions :deep(.el-button) {
  margin-left: 0;
}

.dialog-tip {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--label-3);
}

@keyframes row-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
}

.pkg-table :deep(.el-table__body tr) {
  animation: row-in 0.45s var(--ease-out) both;
}

@media (max-width: 1180px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .search {
    width: 200px;
  }
}
</style>
