<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>用户管理</h1>
        <p>共 {{ total }} 个账号 · 学生、驿站工作人员与管理员统一维护</p>
      </div>
      <el-button type="primary" round :icon="Plus" @click="openCreate">新增用户</el-button>
    </header>

    <section class="toolbar" v-reveal>
      <el-input
        v-model="query.keyword"
        placeholder="搜索姓名、手机号或学号"
        clearable
        :prefix-icon="Search"
        class="search"
        @keyup.enter="search"
        @clear="search"
      />

      <div class="segmented" role="tablist">
        <span class="thumb" :style="{ transform: `translateX(${roleIndex * 100}%)` }"></span>
        <button
          v-for="opt in roleOptions"
          :key="opt.value"
          type="button"
          :class="{ active: query.role === opt.value }"
          @click="setRole(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>

      <el-select v-model="query.status" placeholder="全部状态" clearable class="status-select" @change="search">
        <el-option label="正常" :value="1" />
        <el-option label="禁用" :value="0" />
      </el-select>

      <el-button class="reset" circle :icon="RefreshLeft" title="重置筛选" @click="reset" />
    </section>

    <section class="table-card card" v-reveal="120">
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
        :key="tableKey"
        v-loading="loading"
        :data="rows"
        :row-class-name="rowClass"
        class="user-table stagger-table"
      >
        <el-table-column label="用户" min-width="190">
          <template #default="{ row }">
            <div class="user-cell">
              <span class="mini-avatar" :style="{ background: avatarTint(row.role) }">{{ row.name.slice(0, 1) }}</span>
              <div class="user-text">
                <strong>{{ row.name }}</strong>
                <span>{{ row.student_no || '未填写学号/工号' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <span class="role-badge" :class="row.role">{{ roleLabel(row.role) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="学院 / 部门" min-width="140">
          <template #default="{ row }">{{ row.college || '—' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="96">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              :disabled="row.id === auth.user?.id"
              @change="toggleStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="最近登录" width="145">
          <template #default="{ row }">
            <span class="muted">{{ fmt(row.last_login_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="" width="70" align="right">
          <template #default="{ row }">
            <button class="edit-btn" type="button" @click="openEdit(row)">编辑</button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="load"
          @size-change="load"
        />
      </div>
    </section>

    <el-dialog v-model="createVisible" title="新增用户" width="520px" :close-on-click-modal="false">
      <el-form ref="createRef" :model="createForm" :rules="rules" label-width="92px" class="dialog-form">
        <el-form-item label="角色" prop="role">
          <div class="role-seg">
            <button
              v-for="opt in roleOptions.slice(1)"
              :key="opt.value"
              type="button"
              :class="{ active: createForm.role === opt.value }"
              @click="createForm.role = opt.value"
            >
              {{ opt.label }}
            </button>
          </div>
        </el-form-item>
        <el-form-item label="学号/工号" prop="student_no">
          <el-input v-model="createForm.student_no" placeholder="学生填学号，工作人员填工号" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="createForm.phone" maxlength="11" placeholder="11 位手机号" />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input v-model="createForm.password" show-password placeholder="8-32 位，含字母和数字" />
        </el-form-item>
        <el-form-item label="学院/部门">
          <el-input v-model="createForm.college" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="createVisible = false">取消</el-button>
        <el-button type="primary" round :loading="submitting" @click="submitCreate">创建用户</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑用户" width="480px" :close-on-click-modal="false">
      <el-form ref="editRef" :model="editForm" label-width="92px" class="dialog-form">
        <el-form-item label="账号">
          <el-input :model-value="editForm.student_no || editForm.phone" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option label="学生" value="student" />
            <el-option label="驿站工作人员" value="staff" />
            <el-option label="系统管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="学院/部门">
          <el-input v-model="editForm.college" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="editVisible = false">取消</el-button>
        <el-button type="primary" round :loading="submitting" @click="submitEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { listUsers, createUser, updateUser, updateUserStatus } from '../api/users'

const auth = useAuthStore()

const query = reactive({ page: 1, page_size: 10, keyword: '', role: '', status: '' })
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const tableKey = ref(0)

const createVisible = ref(false)
const editVisible = ref(false)
const submitting = ref(false)
const createRef = ref()
const editRef = ref()

const roleOptions = [
  { label: '全部', value: '' },
  { label: '学生', value: 'student' },
  { label: '工作人员', value: 'staff' },
  { label: '管理员', value: 'admin' }
]

const roleIndex = computed(() => Math.max(roleOptions.findIndex((o) => o.value === query.role), 0))

const createForm = reactive({
  role: 'student',
  student_no: '',
  name: '',
  phone: '',
  password: '',
  college: ''
})

const editForm = reactive({ id: null, student_no: '', phone: '', name: '', role: 'student', college: '' })

const rules = {
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  student_no: [
    {
      validator: (rule, value, callback) => {
        if (createForm.role !== 'student' && !value) {
          callback(new Error('工作人员与管理员必须填写工号'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,32}$/, message: '8-32 位，且包含字母和数字', trigger: 'blur' }
  ]
}

const roleLabel = (r) => ({ student: '学生', staff: '工作人员', admin: '管理员' }[r] || r)
const avatarTint = (r) =>
  ({
    student: 'linear-gradient(145deg,#5ac8fa,#007aff)',
    staff: 'linear-gradient(145deg,#ffd60a,#ff9500)',
    admin: 'linear-gradient(145deg,#bf8bff,#af52de)'
  }[r] || 'linear-gradient(145deg,#c7c7cc,#8e8e93)')

const fmt = (v) => (v ? v.replace('T', ' ').slice(0, 16) : '—')

function rowClass({ row }) {
  if (row._flash === 'on') return 'flash-on'
  if (row._flash === 'off') return 'flash-off'
  return ''
}

function shake(formRef) {
  const el = formRef.value?.$el
  if (!el) return
  el.classList.remove('shake')
  void el.offsetWidth
  el.classList.add('shake')
  window.setTimeout(() => el.classList.remove('shake'), 620)
}

async function load() {
  loading.value = true
  try {
    const data = await listUsers({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      role: query.role || undefined,
      status: query.status === '' ? undefined : query.status
    })
    rows.value = data.items
    total.value = data.total
    tableKey.value += 1
  } finally {
    loading.value = false
  }
}

function search() {
  query.page = 1
  load()
}

function setRole(value) {
  query.role = value
  search()
}

function reset() {
  query.keyword = ''
  query.role = ''
  query.status = ''
  query.page = 1
  load()
}

function openCreate() {
  Object.assign(createForm, {
    role: 'student',
    student_no: '',
    name: '',
    phone: '',
    password: '',
    college: ''
  })
  createVisible.value = true
}

async function submitCreate() {
  await createRef.value.validate(async (valid) => {
    if (!valid) {
      shake(createRef)
      return
    }
    submitting.value = true
    try {
      await createUser({
        ...createForm,
        student_no: createForm.student_no || null,
        college: createForm.college || null
      })
      ElMessage.success('用户创建成功')
      createVisible.value = false
      search()
    } finally {
      submitting.value = false
    }
  })
}

function openEdit(row) {
  Object.assign(editForm, {
    id: row.id,
    student_no: row.student_no || '',
    phone: row.phone,
    name: row.name,
    role: row.role,
    college: row.college || ''
  })
  editVisible.value = true
}

async function submitEdit() {
  submitting.value = true
  try {
    await updateUser(editForm.id, {
      name: editForm.name,
      role: editForm.role,
      college: editForm.college || null
    })
    ElMessage.success('用户信息已更新')
    editVisible.value = false
    load()
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(row) {
  const target = row.status
  try {
    await updateUserStatus(row.id, target)
    ElMessage.success(target === 1 ? '账号已启用' : '账号已禁用')
    row._flash = target === 1 ? 'on' : 'off'
    window.setTimeout(() => {
      row._flash = null
    }, 900)
  } catch (e) {
    row.status = target === 1 ? 0 : 1
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.search {
  width: 250px;
}

.status-select {
  width: 124px;
}

.reset {
  margin-left: auto;
}

.segmented {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 3px;
  border-radius: 12px;
  background: rgba(120, 120, 128, 0.12);
  width: 312px;
}

.segmented .thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: calc((100% - 6px) / 4);
  height: calc(100% - 6px);
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: transform 0.42s var(--spring);
}

.segmented button {
  position: relative;
  z-index: 1;
  height: 30px;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--label-2);
  cursor: pointer;
  border-radius: 9px;
  transition: color 0.2s var(--ease), transform 0.2s var(--spring);
}

.segmented button:active {
  transform: scale(0.95);
}

.segmented button.active {
  color: var(--label);
  font-weight: 600;
}

.table-card {
  padding: 6px 20px 16px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 11px;
}

.mini-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.user-text {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.user-text strong {
  font-size: 13.2px;
  font-weight: 600;
}

.user-text span {
  font-size: 10.8px;
  color: var(--label-3);
}

.role-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 500;
}

.role-badge.student {
  color: #0a6bcb;
  background: rgba(0, 122, 255, 0.1);
}

.role-badge.staff {
  color: #b26500;
  background: rgba(255, 149, 0, 0.13);
}

.role-badge.admin {
  color: #8944ab;
  background: rgba(175, 82, 222, 0.12);
}

.muted {
  color: var(--label-3);
  font-size: 12px;
}

.edit-btn {
  border: none;
  background: transparent;
  color: var(--ios-blue);
  font-size: 12.5px;
  font-family: inherit;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 8px;
  transition: background 0.2s var(--ease), transform 0.2s var(--spring);
}

.edit-btn:hover {
  background: rgba(0, 122, 255, 0.08);
}

.edit-btn:active {
  transform: scale(0.94);
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding: 16px 4px 2px;
}

.dialog-form {
  padding-top: 4px;
}

.role-seg {
  display: inline-flex;
  padding: 3px;
  gap: 2px;
  border-radius: 11px;
  background: rgba(120, 120, 128, 0.12);
}

.role-seg button {
  border: none;
  background: transparent;
  border-radius: 8px;
  padding: 6px 14px;
  font-family: inherit;
  font-size: 12.5px;
  color: var(--label-2);
  cursor: pointer;
  transition: all 0.25s var(--ease);
}

.role-seg button.active {
  background: #fff;
  color: var(--label);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.skeleton {
  padding: 14px 4px 4px;
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
  flex-shrink: 0;
}

.sk-main {
  width: 120px;
  height: 12px;
}

.sk-sub {
  width: 180px;
  height: 10px;
}

.sk-pill {
  width: 92px;
  height: 22px;
  border-radius: 999px;
  margin-left: auto;
}

@keyframes shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

@keyframes skeleton-in {
  to {
    opacity: 1;
  }
}

@keyframes row-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
}

.stagger-table :deep(.el-table__body tr) {
  animation: row-in 0.5s var(--ease-out) both;
}

.stagger-table :deep(.el-table__body tr:nth-child(1)) { animation-delay: 0.02s; }
.stagger-table :deep(.el-table__body tr:nth-child(2)) { animation-delay: 0.06s; }
.stagger-table :deep(.el-table__body tr:nth-child(3)) { animation-delay: 0.1s; }
.stagger-table :deep(.el-table__body tr:nth-child(4)) { animation-delay: 0.14s; }
.stagger-table :deep(.el-table__body tr:nth-child(5)) { animation-delay: 0.18s; }
.stagger-table :deep(.el-table__body tr:nth-child(6)) { animation-delay: 0.22s; }
.stagger-table :deep(.el-table__body tr:nth-child(7)) { animation-delay: 0.26s; }
.stagger-table :deep(.el-table__body tr:nth-child(8)) { animation-delay: 0.3s; }
.stagger-table :deep(.el-table__body tr:nth-child(9)) { animation-delay: 0.34s; }
.stagger-table :deep(.el-table__body tr:nth-child(10)) { animation-delay: 0.38s; }

.stagger-table :deep(.el-table__body tr.flash-on > td.el-table__cell) {
  animation: flash-green 0.9s var(--ease);
}

.stagger-table :deep(.el-table__body tr.flash-off > td.el-table__cell) {
  animation: flash-gray 0.9s var(--ease);
}

@keyframes flash-green {
  0% {
    background: rgba(52, 199, 89, 0.18);
  }
  100% {
    background: transparent;
  }
}

@keyframes flash-gray {
  0% {
    background: rgba(120, 120, 128, 0.16);
  }
  100% {
    background: transparent;
  }
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

@media (max-width: 900px) {
  .search {
    width: 100%;
  }
  .segmented {
    width: 100%;
  }
  .reset {
    margin-left: 0;
  }
}
</style>
