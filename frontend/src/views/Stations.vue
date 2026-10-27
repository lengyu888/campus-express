<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>驿站管理</h1>
        <p>{{ stations.length }} 个驿站 · {{ totalShelves }} 个货架 · {{ totalCapacity }} 个格口</p>
      </div>
      <el-button v-if="isAdmin" type="primary" round :icon="Plus" @click="openCreate">新增驿站</el-button>
    </header>

    <section class="stats">
      <article v-for="(item, i) in statCards" :key="item.label" class="stat card" v-reveal="i * 60">
        <div class="stat-icon" :style="{ background: item.tint, color: item.color }">
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-label">{{ item.label }}</span>
          <strong class="stat-value">{{ item.value }}</strong>
          <span class="stat-hint">{{ item.hint }}</span>
        </div>
      </article>
    </section>

    <section v-if="loading" class="grid">
      <div v-for="i in 2" :key="i" class="station card skeleton-card">
        <div class="sk-line w40"></div>
        <div class="sk-line w70"></div>
        <div class="sk-block"></div>
      </div>
    </section>

    <section v-else-if="!stations.length" class="empty card" v-reveal>
      <div class="empty-icon"><el-icon :size="26"><OfficeBuilding /></el-icon></div>
      <h3>还没有驿站</h3>
      <p>创建第一个驿站后，就可以添加货架并分配格口。</p>
      <el-button v-if="isAdmin" type="primary" round :icon="Plus" @click="openCreate">新增驿站</el-button>
    </section>

    <section v-else class="grid">
      <article
        v-for="(st, i) in stations"
        :key="st.id"
        class="station card"
        v-reveal="i * 70"
      >
        <div class="station-head">
          <div class="icon" :class="{ off: st.status === 0 }">
            <el-icon :size="20"><OfficeBuilding /></el-icon>
          </div>
          <div class="titles">
            <h3>{{ st.name }}</h3>
            <span class="sub">
              {{ st.code }}
              <i class="status-dot" :class="{ on: st.status === 1 }"></i>
              {{ st.status === 1 ? '营业中' : '已停用' }}
            </span>
          </div>
          <el-dropdown v-if="isAdmin" trigger="click" @command="(cmd) => onStationCommand(cmd, st)">
            <button class="more" type="button" aria-label="更多操作">
              <el-icon :size="16"><MoreFilled /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">编辑信息</el-dropdown-item>
                <el-dropdown-item command="status" divided>
                  {{ st.status === 1 ? '停用驿站' : '启用驿站' }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="info">
          <span><el-icon :size="14"><Location /></el-icon>{{ st.address }}</span>
          <span><el-icon :size="14"><Clock /></el-icon>{{ st.open_time }} — {{ st.close_time }}</span>
          <span><el-icon :size="14"><UserFilled /></el-icon>{{ st.manager_name || '未指定负责人' }}</span>
        </div>

        <div class="capacity">
          <div class="cap-top">
            <span>格口占用</span>
            <strong class="tabular">{{ st.used_count }} / {{ st.capacity }}</strong>
          </div>
          <div class="bar">
            <span :class="level(st.occupancy)" :style="{ width: pct(st.occupancy) }"></span>
          </div>
          <div class="cap-bottom">
            <span>{{ st.shelf_count }} 个货架</span>
            <span class="tabular">{{ pct(st.occupancy) }}</span>
          </div>
        </div>

        <div v-if="st.shelves.length" class="shelf-chips">
          <span v-for="sh in st.shelves.slice(0, 4)" :key="sh.id" class="chip">{{ sh.code }}</span>
          <span v-if="st.shelves.length > 4" class="chip muted">+{{ st.shelves.length - 4 }}</span>
        </div>

        <div class="actions">
          <button class="link" type="button" @click="openShelves(st)">
            货架管理
            <el-icon :size="13"><ArrowRight /></el-icon>
          </button>
          <button v-if="isAdmin" class="edit-link" type="button" @click="openEdit(st)">编辑</button>
        </div>
      </article>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑驿站' : '新增驿站'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px" class="dialog-form">
        <el-form-item label="驿站编码" prop="code">
          <el-input v-model="form.code" :disabled="Boolean(editing)" placeholder="如 ST-A" />
        </el-form-item>
        <el-form-item label="驿站名称" prop="name">
          <el-input v-model="form.name" placeholder="如 东区驿站" />
        </el-form-item>
        <el-form-item label="详细地址" prop="address">
          <el-input v-model="form.address" placeholder="楼栋、楼层等" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" maxlength="11" placeholder="选填，11 位手机号" />
        </el-form-item>
        <el-form-item label="营业时间" required>
          <div class="time-row">
            <el-time-select v-model="form.open_time" start="06:00" end="23:30" step="00:30" placeholder="开始" />
            <span class="time-sep">至</span>
            <el-time-select v-model="form.close_time" start="06:00" end="23:30" step="00:30" placeholder="结束" />
          </div>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="form.manager_id" clearable placeholder="选填，指定工作人员" style="width: 100%">
            <el-option v-for="m in managers" :key="m.id" :label="`${m.name}（${m.student_no}）`" :value="m.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" round :loading="submitting" @click="submitStation">
          {{ editing ? '保存修改' : '创建驿站' }}
        </el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" :with-header="false" size="480px" class="shelf-drawer">
      <div class="drawer-head">
        <div>
          <h3>{{ activeStation?.name }}</h3>
          <span>{{ activeStation?.code }} · {{ shelves.length }} 个货架</span>
        </div>
        <div class="drawer-actions">
          <el-button v-if="isAdmin" type="primary" round size="small" :icon="Plus" @click="openShelfCreate">
            新增货架
          </el-button>
          <button class="drawer-close" type="button" aria-label="关闭" @click="drawerVisible = false">
            <el-icon :size="16"><Close /></el-icon>
          </button>
        </div>
      </div>

      <div class="drawer-summary" v-if="activeStation">
        <div class="summary-item">
          <span>总格口</span>
          <strong>{{ shelves.reduce((n, s) => n + s.capacity, 0) }}</strong>
        </div>
        <div class="summary-item">
          <span>已用</span>
          <strong>{{ shelves.reduce((n, s) => n + s.used_count, 0) }}</strong>
        </div>
        <div class="summary-item">
          <span>占用率</span>
          <strong>{{ drawerOccupancy }}%</strong>
        </div>
      </div>

      <div v-if="shelfLoading" class="drawer-loading">正在加载货架…</div>
      <div v-else-if="!shelves.length" class="drawer-empty">
        <el-icon :size="24"><Box /></el-icon>
        <p>暂无货架，先添加一个吧</p>
      </div>
      <div v-else class="shelf-list">
        <div v-for="sh in shelves" :key="sh.id" class="shelf-row">
          <div class="shelf-code">{{ sh.code }}</div>
          <div class="shelf-main">
            <div class="shelf-meta">
              <span>{{ sh.zone || '未分区' }}</span>
              <strong class="tabular">{{ sh.used_count }} / {{ sh.capacity }}</strong>
            </div>
            <div class="bar small">
              <span :class="level(sh.occupancy)" :style="{ width: pct(sh.occupancy) }"></span>
            </div>
          </div>
          <div v-if="isAdmin" class="shelf-actions">
            <button type="button" aria-label="编辑货架" @click="openShelfEdit(sh)">
              <el-icon :size="14"><EditPen /></el-icon>
            </button>
            <button type="button" class="danger" aria-label="删除货架" @click="removeShelf(sh)">
              <el-icon :size="14"><Delete /></el-icon>
            </button>
          </div>
        </div>
      </div>
    </el-drawer>

    <el-dialog
      v-model="shelfDialogVisible"
      :title="shelfEditing ? '编辑货架' : '新增货架'"
      width="440px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form ref="shelfFormRef" :model="shelfForm" :rules="shelfRules" label-width="86px">
        <el-form-item label="货架编号" prop="code">
          <el-input v-model="shelfForm.code" placeholder="如 A-01" />
        </el-form-item>
        <el-form-item label="分区">
          <el-input v-model="shelfForm.zone" placeholder="如 A 区（选填）" />
        </el-form-item>
        <el-form-item label="格口容量" prop="capacity">
          <el-input-number v-model="shelfForm.capacity" :min="1" :max="200" :step="1" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="shelfDialogVisible = false">取消</el-button>
        <el-button type="primary" round :loading="shelfSubmitting" @click="submitShelf">
          {{ shelfEditing ? '保存修改' : '创建货架' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, MoreFilled, Location, Clock, UserFilled, ArrowRight,
  OfficeBuilding, Box, EditPen, Delete, Close
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { listUsers } from '../api/users'
import {
  listStations, createStation, updateStation, updateStationStatus,
  listShelves, createShelf, updateShelf, deleteShelf
} from '../api/stations'

const auth = useAuthStore()
const isAdmin = computed(() => auth.role === 'admin')

const stations = ref([])
const loading = ref(true)
const managers = ref([])

const totalShelves = computed(() => stations.value.reduce((n, s) => n + s.shelf_count, 0))
const totalCapacity = computed(() => stations.value.reduce((n, s) => n + s.capacity, 0))
const totalUsed = computed(() => stations.value.reduce((n, s) => n + s.used_count, 0))
const avgOccupancy = computed(() =>
  totalCapacity.value ? Math.round((totalUsed.value / totalCapacity.value) * 100) : 0
)

const statCards = computed(() => [
  { label: '驿站数量', value: stations.value.length, hint: '在运营服务点', icon: OfficeBuilding, tint: 'rgba(0,122,255,.12)', color: '#007aff' },
  { label: '货架数量', value: totalShelves.value, hint: '含分区货架', icon: Box, tint: 'rgba(52,199,89,.13)', color: '#248a3d' },
  { label: '总格口', value: totalCapacity.value, hint: '可存放包裹', icon: OfficeBuilding, tint: 'rgba(255,149,0,.14)', color: '#c26a00' },
  { label: '平均占用率', value: `${avgOccupancy.value}%`, hint: '全站合计', icon: Box, tint: 'rgba(175,82,222,.12)', color: '#8944ab' }
])

const formRef = ref()
const dialogVisible = ref(false)
const editing = ref(null)
const submitting = ref(false)
const form = reactive({
  code: '',
  name: '',
  address: '',
  phone: '',
  open_time: '08:00',
  close_time: '21:00',
  manager_id: null
})

const rules = {
  code: [
    { required: true, message: '请输入驿站编码', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9-]{2,20}$/, message: '2-20 位字母、数字或中划线', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入驿站名称', trigger: 'blur' }],
  address: [{ required: true, message: '请输入详细地址', trigger: 'blur' }],
  phone: [{ pattern: /^1\d{10}$/, message: '请输入 11 位手机号', trigger: 'blur' }]
}

const drawerVisible = ref(false)
const activeStation = ref(null)
const shelves = ref([])
const shelfLoading = ref(false)

const shelfFormRef = ref()
const shelfDialogVisible = ref(false)
const shelfEditing = ref(null)
const shelfSubmitting = ref(false)
const shelfForm = reactive({ code: '', zone: '', capacity: 20 })

const shelfRules = {
  code: [{ required: true, message: '请输入货架编号', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }]
}

const drawerOccupancy = computed(() => {
  const cap = shelves.value.reduce((n, s) => n + s.capacity, 0)
  const used = shelves.value.reduce((n, s) => n + s.used_count, 0)
  return cap ? Math.round((used / cap) * 100) : 0
})

const pct = (v) => `${Math.round((v || 0) * 100)}%`
const level = (v) => {
  const n = v || 0
  if (n >= 0.85) return 'high'
  if (n >= 0.6) return 'mid'
  return 'low'
}

async function load() {
  loading.value = true
  try {
    const data = await listStations()
    stations.value = data.items || []
  } finally {
    loading.value = false
  }
}

async function loadManagers() {
  if (!isAdmin.value) return
  try {
    const data = await listUsers({ role: 'staff', page: 1, page_size: 100 })
    managers.value = data.items || []
  } catch (e) {
    managers.value = []
  }
}

function resetForm() {
  Object.assign(form, {
    code: '',
    name: '',
    address: '',
    phone: '',
    open_time: '08:00',
    close_time: '21:00',
    manager_id: null
  })
}

function openCreate() {
  editing.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(station) {
  editing.value = station.id
  Object.assign(form, {
    code: station.code,
    name: station.name,
    address: station.address,
    phone: station.phone || '',
    open_time: station.open_time || '08:00',
    close_time: station.close_time || '21:00',
    manager_id: station.manager_id || null
  })
  dialogVisible.value = true
}

async function submitStation() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (form.close_time <= form.open_time) {
      ElMessage.error('结束时间必须晚于开始时间')
      return
    }
    submitting.value = true
    try {
      const payload = {
        code: form.code,
        name: form.name,
        address: form.address,
        phone: form.phone || null,
        open_time: form.open_time,
        close_time: form.close_time,
        manager_id: form.manager_id || null
      }
      if (editing.value) {
        delete payload.code
        await updateStation(editing.value, payload)
        ElMessage.success('驿站信息已更新')
      } else {
        await createStation(payload)
        ElMessage.success('驿站创建成功')
      }
      dialogVisible.value = false
      load()
    } finally {
      submitting.value = false
    }
  })
}

async function onStationCommand(command, station) {
  if (command === 'edit') {
    openEdit(station)
    return
  }
  if (command === 'status') {
    const next = station.status === 1 ? 0 : 1
    const action = next === 1 ? '启用' : '停用'
    await ElMessageBox.confirm(`确定${action}「${station.name}」吗？`, '提示', {
      confirmButtonText: action,
      cancelButtonText: '取消',
      type: 'warning'
    })
    await updateStationStatus(station.id, next)
    ElMessage.success(`驿站已${action}`)
    load()
  }
}

async function openShelves(station) {
  activeStation.value = station
  shelves.value = []
  drawerVisible.value = true
  shelfLoading.value = true
  try {
    const data = await listShelves(station.id)
    shelves.value = data.items || []
    activeStation.value = data.station || station
  } finally {
    shelfLoading.value = false
  }
}

async function refreshShelves() {
  if (!activeStation.value) return
  const data = await listShelves(activeStation.value.id)
  shelves.value = data.items || []
  activeStation.value = data.station
  await load()
}

function openShelfCreate() {
  shelfEditing.value = null
  Object.assign(shelfForm, { code: '', zone: '', capacity: 20 })
  shelfDialogVisible.value = true
}

function openShelfEdit(shelf) {
  shelfEditing.value = shelf.id
  Object.assign(shelfForm, {
    code: shelf.code,
    zone: shelf.zone || '',
    capacity: shelf.capacity
  })
  shelfDialogVisible.value = true
}

async function submitShelf() {
  await shelfFormRef.value.validate(async (valid) => {
    if (!valid) return
    shelfSubmitting.value = true
    try {
      const payload = {
        code: shelfForm.code,
        zone: shelfForm.zone || null,
        capacity: shelfForm.capacity
      }
      if (shelfEditing.value) {
        await updateShelf(shelfEditing.value, payload)
        ElMessage.success('货架信息已更新')
      } else {
        await createShelf(activeStation.value.id, payload)
        ElMessage.success('货架创建成功')
      }
      shelfDialogVisible.value = false
      await refreshShelves()
    } finally {
      shelfSubmitting.value = false
    }
  })
}

async function removeShelf(shelf) {
  await ElMessageBox.confirm(`确定删除货架「${shelf.code}」吗？`, '删除货架', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  })
  await deleteShelf(shelf.id)
  ElMessage.success('货架已删除')
  await refreshShelves()
}

onMounted(() => {
  load()
  loadManagers()
})
</script>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  transition: transform 0.35s var(--spring), box-shadow 0.35s var(--ease);
}

.stat:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
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
}

.stat-label {
  font-size: 11.5px;
  color: var(--label-3);
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 2px 0 1px;
  font-variant-numeric: tabular-nums;
}

.stat-hint {
  font-size: 10.5px;
  color: var(--label-4);
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.station {
  padding: 22px 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: transform 0.35s var(--spring), box-shadow 0.35s var(--ease);
}

.station:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.station-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(145deg, #e8f3ff, #d7e9ff);
  color: var(--ios-blue);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon.off {
  background: rgba(120, 120, 128, 0.1);
  color: var(--label-3);
}

.titles {
  flex: 1;
  min-width: 0;
}

.titles h3 {
  margin: 0 0 4px;
  font-size: 16.5px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.sub {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--label-3);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--label-4);
  margin-left: 4px;
}

.status-dot.on {
  background: var(--ios-green);
  box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.14);
}

.more {
  border: none;
  background: transparent;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  color: var(--label-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s var(--ease);
}

.more:hover {
  background: rgba(120, 120, 128, 0.1);
}

.info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 12.5px;
  color: var(--label-2);
}

.info span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info .el-icon {
  color: var(--label-4);
}

.capacity {
  padding: 13px 14px;
  border-radius: 14px;
  background: rgba(120, 120, 128, 0.06);
}

.cap-top,
.cap-bottom {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 11.5px;
  color: var(--label-3);
}

.cap-top strong {
  font-size: 13px;
  color: var(--label);
  font-weight: 600;
}

.bar {
  height: 6px;
  border-radius: 999px;
  background: rgba(120, 120, 128, 0.16);
  overflow: hidden;
  margin: 8px 0 7px;
}

.bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #4aa3ff, #007aff);
  transition: width 0.8s var(--ease-out);
}

.bar span.mid {
  background: linear-gradient(90deg, #ffc24a, #ff9500);
}

.bar span.high {
  background: linear-gradient(90deg, #ff8a80, #ff3b30);
}

.bar.small {
  height: 4px;
  margin: 6px 0 0;
}

.shelf-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip {
  font-size: 10.5px;
  color: var(--label-2);
  background: rgba(120, 120, 128, 0.09);
  border-radius: 7px;
  padding: 3px 8px;
  font-family: "SF Mono", Consolas, monospace;
}

.chip.muted {
  color: var(--label-3);
}

.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--separator);
  padding-top: 12px;
  margin-top: auto;
}

.link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: var(--ios-blue);
  font-family: inherit;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 2px;
  border-radius: 8px;
  transition: gap 0.25s var(--spring), opacity 0.2s;
}

.link:hover {
  gap: 8px;
}

.edit-link {
  border: none;
  background: transparent;
  color: var(--label-2);
  font-family: inherit;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 9px;
  border-radius: 8px;
  transition: background 0.2s var(--ease), color 0.2s var(--ease), transform 0.2s var(--spring);
}

.edit-link:hover {
  background: rgba(120, 120, 128, 0.1);
  color: var(--label);
}

.edit-link:active {
  transform: scale(0.94);
}

.empty {
  padding: 60px 30px;
  text-align: center;
}

.empty-icon {
  width: 58px;
  height: 58px;
  margin: 0 auto 14px;
  border-radius: 18px;
  background: rgba(0, 122, 255, 0.1);
  color: var(--ios-blue);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty h3 {
  margin: 0 0 6px;
  font-size: 17px;
}

.empty p {
  margin: 0 0 18px;
  color: var(--label-3);
  font-size: 12.5px;
}

.dialog-form {
  padding-top: 4px;
}

.time-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.time-row :deep(.el-select) {
  flex: 1;
}

.time-sep {
  color: var(--label-3);
  font-size: 12px;
}

/* 抽屉 */
.drawer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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
  transition: background 0.2s var(--ease), transform 0.2s var(--spring);
}

.drawer-close:hover {
  background: rgba(120, 120, 128, 0.16);
}

.drawer-close:active {
  transform: scale(0.92);
}

.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 4px 0 18px;
  border-bottom: 1px solid var(--separator);
}

.drawer-head h3 {
  margin: 0 0 4px;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.drawer-head span {
  font-size: 11.5px;
  color: var(--label-3);
}

.drawer-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 18px 0;
}

.summary-item {
  padding: 12px;
  border-radius: 13px;
  background: rgba(120, 120, 128, 0.06);
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.summary-item span {
  font-size: 11px;
  color: var(--label-3);
}

.summary-item strong {
  font-size: 19px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.shelf-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shelf-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 13px 14px;
  border-radius: 14px;
  background: rgba(120, 120, 128, 0.06);
  transition: background 0.2s var(--ease);
}

.shelf-row:hover {
  background: rgba(120, 120, 128, 0.1);
}

.shelf-code {
  width: 54px;
  font-family: "SF Mono", Consolas, monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--label);
  flex-shrink: 0;
}

.shelf-main {
  flex: 1;
  min-width: 0;
}

.shelf-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11.5px;
  color: var(--label-3);
}

.shelf-meta strong {
  color: var(--label);
  font-weight: 600;
}

.shelf-actions {
  display: flex;
  gap: 2px;
}

.shelf-actions button {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 8px;
  color: var(--label-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, color 0.2s, transform 0.2s var(--spring);
}

.shelf-actions button:hover {
  background: rgba(255, 255, 255, 0.9);
  color: var(--ios-blue);
}

.shelf-actions button.danger:hover {
  color: var(--ios-red);
}

.shelf-actions button:active {
  transform: scale(0.9);
}

.drawer-loading,
.drawer-empty {
  padding: 40px 20px;
  text-align: center;
  color: var(--label-3);
  font-size: 12.5px;
}

.drawer-empty .el-icon {
  color: var(--label-4);
  margin-bottom: 8px;
}

.skeleton-card {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sk-line,
.sk-block {
  background: linear-gradient(90deg, rgba(120, 120, 128, 0.1) 25%, rgba(120, 120, 128, 0.16) 37%, rgba(120, 120, 128, 0.1) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
  border-radius: 9px;
}

.sk-line {
  height: 14px;
}

.sk-line.w40 {
  width: 40%;
}

.sk-line.w70 {
  width: 70%;
}

.sk-block {
  height: 120px;
}

@keyframes shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

@media (max-width: 1100px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
