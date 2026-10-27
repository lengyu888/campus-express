<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>个人中心</h1>
        <p>查看账号信息，管理登录密码与安全设置</p>
      </div>
    </header>

    <div class="grid">
      <section class="profile card" v-reveal>
        <div class="profile-top">
          <div class="avatar-ring">
            <div class="avatar">{{ (auth.user?.name || '?').slice(0, 1) }}</div>
          </div>
          <div class="profile-title">
            <h2>{{ auth.user?.name }}</h2>
            <span class="role-pill" :class="auth.user?.role">{{ auth.roleLabel }}</span>
          </div>
        </div>

        <div class="group">
          <div v-for="row in infoRows" :key="row.label" class="row">
            <span class="row-label">{{ row.label }}</span>
            <span class="row-value" :class="{ muted: !row.value }">{{ row.value || '—' }}</span>
          </div>
        </div>

        <div class="status-note">
          <el-icon :size="16"><Lock /></el-icon>
          <span>账号已启用双重校验：密码 + 令牌有效期管理</span>
        </div>
      </section>

      <section class="security card" v-reveal="100">
        <div class="panel-head">
          <h3>修改密码</h3>
          <p>修改成功后需要使用新密码重新登录</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="pwd-form">
          <el-form-item label="原密码" prop="old_password">
            <el-input v-model="form.old_password" type="password" show-password placeholder="请输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="form.new_password" type="password" show-password placeholder="8-32 位，含字母和数字" />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirm">
            <el-input v-model="form.confirm" type="password" show-password placeholder="再次输入新密码" />
          </el-form-item>
          <div class="actions">
            <el-button round @click="resetForm">重置</el-button>
            <el-button type="primary" round :loading="submitting" :class="{ saved }" @click="submit">
              <el-icon v-if="saved" :size="15"><Check /></el-icon>
              <span>{{ saved ? '已保存' : '保存新密码' }}</span>
            </el-button>
          </div>
        </el-form>
      </section>

      <section class="motion-card card" v-reveal="180">
        <div class="panel-head">
          <h3>体验与动效</h3>
          <p>控制界面动画强度。跟随系统时会尊重"减少动态效果"设置，并根据设备性能自动降级。</p>
        </div>
        <div class="motion-row">
          <div class="seg" role="group" aria-label="动效偏好">
            <button
              v-for="opt in motionOptions"
              :key="opt.value"
              type="button"
              :class="{ active: motionPref === opt.value }"
              @click="chooseMotion(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
          <span class="motion-state">
            当前：{{ tierLabel }}
            <span class="tier-dot" :class="motionTier"></span>
          </span>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Check } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { motionPref, motionTier, setMotionPref } from '../motion'
import { changePassword } from '../api/auth'
import { tokenStore } from '../api/http'

const auth = useAuthStore()
const router = useRouter()
const formRef = ref()
const submitting = ref(false)

const form = reactive({ old_password: '', new_password: '', confirm: '' })
const saved = ref(false)

const motionOptions = [
  { label: '跟随系统', value: 'auto' },
  { label: '完整动效', value: 'full' },
  { label: '精简动效', value: 'reduced' }
]

const tierLabel = computed(() => {
  if (motionPref.value === 'reduced') return '精简'
  if (motionTier.value === 'low') return '低配自适应'
  if (motionTier.value === 'reduced') return '精简（系统偏好）'
  return '完整'
})

function chooseMotion(value) {
  setMotionPref(value)
}

const infoRows = computed(() => [
  { label: '学号 / 工号', value: auth.user?.student_no },
  { label: '手机号', value: auth.user?.phone },
  { label: '学院 / 部门', value: auth.user?.college },
  { label: '账号状态', value: auth.user?.status === 1 ? '正常' : '已禁用' },
  { label: '注册时间', value: fmt(auth.user?.created_at) },
  { label: '最近登录', value: fmt(auth.user?.last_login_at) }
])

const rules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,32}$/, message: '8-32 位，且包含字母和数字', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.new_password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

function fmt(v) {
  return v ? v.replace('T', ' ').slice(0, 16) : ''
}

function resetForm() {
  form.old_password = ''
  form.new_password = ''
  form.confirm = ''
  formRef.value?.clearValidate()
}

async function submit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await changePassword({ old_password: form.old_password, new_password: form.new_password })
      saved.value = true
      ElMessage.success('密码修改成功，请重新登录')
      if (motionTier.value !== 'reduced') {
        await new Promise((resolve) => setTimeout(resolve, 520))
      }
      tokenStore.clear()
      auth.user = null
      router.replace('/login')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  max-width: 1080px;
}

.profile {
  padding: 30px 28px 24px;
}

.profile-top {
  display: flex;
  align-items: center;
  gap: 18px;
  padding-bottom: 26px;
}

.avatar-ring {
  width: 74px;
  height: 74px;
  border-radius: 50%;
  padding: 3px;
  background: linear-gradient(145deg, #5ac8fa, #007aff 55%, #af52de);
  box-shadow: 0 10px 22px rgba(0, 122, 255, 0.22);
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 600;
  color: var(--ios-blue);
}

.profile-title h2 {
  margin: 0 0 7px;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.role-pill {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 500;
}

.role-pill.student {
  color: #0a6bcb;
  background: rgba(0, 122, 255, 0.1);
}

.role-pill.staff {
  color: #b26500;
  background: rgba(255, 149, 0, 0.13);
}

.role-pill.admin {
  color: #8944ab;
  background: rgba(175, 82, 222, 0.12);
}

.group {
  border-radius: 18px;
  background: rgba(120, 120, 128, 0.06);
  overflow: hidden;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 13px 16px;
  border-bottom: 1px solid rgba(60, 60, 67, 0.07);
  font-size: 13px;
}

.row:last-child {
  border-bottom: none;
}

.row-label {
  color: var(--label-3);
  flex-shrink: 0;
}

.row-value {
  color: var(--label);
  font-weight: 500;
  text-align: right;
  word-break: break-all;
}

.row-value.muted {
  color: var(--label-4);
  font-weight: 400;
}

.status-note {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 18px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(52, 199, 89, 0.09);
  color: #248a3d;
  font-size: 11.5px;
}

.security {
  padding: 30px 28px;
}

.panel-head {
  margin-bottom: 22px;
}

.panel-head h3 {
  margin: 0 0 5px;
  font-size: 17px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.panel-head p {
  margin: 0;
  font-size: 12px;
  color: var(--label-3);
}

.pwd-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.pwd-form :deep(.el-form-item__label) {
  padding-bottom: 7px !important;
  font-size: 12.5px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 6px;
}

.el-button.saved {
  background: var(--ios-green);
  border-color: var(--ios-green);
  box-shadow: 0 8px 20px rgba(52, 199, 89, 0.28);
}

.motion-card {
  grid-column: 1 / -1;
  padding: 26px 28px;
}

.motion-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
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
  padding: 7px 18px;
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

.motion-state {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: var(--label-3);
}

.tier-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ios-blue);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.tier-dot.low {
  background: var(--ios-orange);
  box-shadow: 0 0 0 3px rgba(255, 149, 0, 0.16);
}

.tier-dot.reduced {
  background: var(--label-4);
  box-shadow: 0 0 0 3px rgba(120, 120, 128, 0.14);
}

@media (max-width: 1000px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
