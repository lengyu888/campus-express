<template>
  <div class="login-page">
    <div class="blob b1"></div>
    <div class="blob b2"></div>
    <div class="blob b3"></div>

    <section class="login-card" :class="{ leaving, success }">
      <div class="logo">
        <svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 8.5 12 3 3 8.5v7L12 21l9-5.5z" />
          <path d="M3 8.5 12 14l9-5.5M12 14v7" />
        </svg>
      </div>

      <h1>校园快递收发系统</h1>
      <p class="subtitle">Campus Express · 让每一件快递准确送达</p>

      <el-form ref="formRef" :model="form" :rules="rules" class="form" @submit.prevent="onSubmit">
        <el-form-item prop="account">
          <el-input
            v-model="form.account"
            size="large"
            placeholder="学号 / 工号 / 手机号"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            size="large"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="onSubmit"
          />
        </el-form-item>

        <el-button
          type="primary"
          class="submit"
          :class="{ success }"
          :loading="auth.loading && !success"
          @click="onSubmit"
        >
          <el-icon v-if="success" :size="18"><Check /></el-icon>
          <span>{{ success ? '登录成功，正在进入' : '登录' }}</span>
        </el-button>
      </el-form>

      <div class="divider"><span>演示账号 · 点击自动填充</span></div>

      <div class="demo">
        <button
          v-for="(item, i) in demos"
          :key="item.account"
          type="button"
          class="demo-item"
          :class="{ active: selected === i }"
          @click="fill(item, i)"
        >
          <span class="demo-avatar" :style="{ background: item.color }">{{ item.label[0] }}</span>
          <span class="demo-info">
            <strong>{{ item.label }}</strong>
            <span>{{ item.account }} · {{ item.password }}</span>
          </span>
          <el-icon class="check" :size="15"><Check /></el-icon>
        </button>
      </div>

      <p class="foot">软件工程课程设计 · 数据仅用于教学演示</p>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Check } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { motionTier } from '../motion'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const formRef = ref()
const form = reactive({ account: '', password: '' })
const selected = ref(-1)
const success = ref(false)
const leaving = ref(false)

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const rules = {
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const demos = [
  { label: '管理员', account: 'admin', password: 'Admin@123', color: 'linear-gradient(145deg,#ff9f0a,#ff6b00)' },
  { label: '工作人员', account: 'staff01', password: 'Staff@123', color: 'linear-gradient(145deg,#5ac8fa,#007aff)' },
  { label: '学生', account: '2023010101', password: 'Student@123', color: 'linear-gradient(145deg,#30d158,#248a3d)' }
]

function fill(item, index) {
  form.account = item.account
  form.password = item.password
  selected.value = index
}

async function onSubmit() {
  if (auth.loading) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await auth.login({ ...form })
      success.value = true
      ElMessage.success('登录成功，正在进入系统')
      const reduced = motionTier.value === 'reduced'
      if (!reduced) await wait(420)
      leaving.value = true
      if (!reduced) await wait(380)
      const redirect = route.query.redirect ? String(route.query.redirect) : '/'
      router.replace(redirect)
    } catch (e) {
      // 错误提示由拦截器统一处理
    }
  })
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  overflow: hidden;
  background: #f5f5f7;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.55;
  will-change: transform;
}

.b1 {
  width: 560px;
  height: 560px;
  top: -180px;
  left: -140px;
  background: radial-gradient(circle at 35% 35%, #8ecbff, #007aff 70%);
  animation: float-slow 16s ease-in-out infinite;
}

.b2 {
  width: 520px;
  height: 520px;
  right: -160px;
  bottom: -200px;
  background: radial-gradient(circle at 60% 40%, #e0b3ff, #af52de 70%);
  animation: float-slow 19s ease-in-out infinite reverse;
}

.b3 {
  width: 320px;
  height: 320px;
  right: 12vw;
  top: -120px;
  background: radial-gradient(circle at 50% 50%, #b8f5e6, #30b0c7 70%);
  opacity: 0.4;
  animation: float-slow 22s ease-in-out infinite;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 424px;
  padding: 40px 38px 26px;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(36px) saturate(180%);
  -webkit-backdrop-filter: blur(36px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02), 0 30px 80px rgba(31, 45, 61, 0.16);
  animation: card-in 0.8s var(--ease-out) both;
  transition: opacity 0.4s var(--ease), transform 0.5s var(--ease), filter 0.4s var(--ease);
}

.login-card.leaving {
  opacity: 0;
  transform: translateY(-14px) scale(1.035);
  filter: blur(10px);
}

.login-card.success {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02), 0 34px 90px rgba(0, 122, 255, 0.22);
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(28px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.logo {
  width: 58px;
  height: 58px;
  border-radius: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(145deg, #33a1ff 0%, #007aff 55%, #5856d6 100%);
  box-shadow: 0 12px 26px rgba(0, 122, 255, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.45);
  margin-bottom: 22px;
}

h1 {
  margin: 0 0 7px;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--label);
}

.subtitle {
  margin: 0 0 28px;
  font-size: 13px;
  color: var(--label-3);
  letter-spacing: 0;
}

.form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.form :deep(.el-input__wrapper) {
  height: 48px;
  border-radius: 14px;
}

.form :deep(.el-input__wrapper.is-focus .el-input__icon) {
  color: var(--ios-blue);
}

.submit {
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 50px;
  margin-top: 6px;
  border-radius: 15px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.04em;
  background: linear-gradient(180deg, #1a8cff, #007aff);
  box-shadow: 0 10px 24px rgba(0, 122, 255, 0.3);
  transition: background 0.4s var(--ease), box-shadow 0.4s var(--ease), transform 0.2s var(--spring);
}

.submit.success {
  background: linear-gradient(180deg, #3ddc6a, #34c759);
  box-shadow: 0 10px 26px rgba(52, 199, 89, 0.35);
}

.submit.success :deep(span) {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.submit::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 20%, rgba(255, 255, 255, 0.35) 50%, transparent 80%);
  transform: translateX(-120%);
}

.submit:hover::after {
  animation: sheen 0.9s var(--ease-out);
}

@keyframes sheen {
  to {
    transform: translateX(120%);
  }
}

.divider {
  position: relative;
  text-align: center;
  margin: 30px 0 14px;
  color: var(--label-3);
  font-size: 11px;
  letter-spacing: 0.02em;
}

.divider::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  background: var(--separator);
}

.divider span {
  position: relative;
  padding: 0 12px;
  background: transparent;
}

.demo {
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  overflow: hidden;
  background: rgba(120, 120, 128, 0.07);
}

.demo-item {
  animation: demo-in 0.55s var(--ease-out) both;
}

.demo-item:nth-child(1) {
  animation-delay: 0.34s;
}

.demo-item:nth-child(2) {
  animation-delay: 0.42s;
}

.demo-item:nth-child(3) {
  animation-delay: 0.5s;
}

@keyframes demo-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
}

.demo-item {
  display: flex;
  align-items: center;
  gap: 11px;
  width: 100%;
  padding: 11px 14px;
  border: none;
  border-bottom: 1px solid rgba(60, 60, 67, 0.07);
  background: transparent;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s var(--ease), transform 0.2s var(--spring);
}

.demo-item:last-child {
  border-bottom: none;
}

.demo-item:hover {
  background: rgba(255, 255, 255, 0.65);
}

.demo-item:active {
  transform: scale(0.985);
}

.demo-item.active {
  background: rgba(0, 122, 255, 0.08);
}

.demo-avatar {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.demo-info {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
  flex: 1;
  min-width: 0;
}

.demo-info strong {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--label);
}

.demo-info span {
  font-size: 10.5px;
  color: var(--label-3);
  font-family: "SF Mono", Consolas, monospace;
  letter-spacing: 0;
}

.check {
  color: var(--ios-blue);
  opacity: 0;
  transform: scale(0.6);
  transition: opacity 0.2s var(--ease), transform 0.3s var(--spring);
}

.demo-item.active .check {
  opacity: 1;
  transform: scale(1);
}

.foot {
  margin: 22px 0 0;
  text-align: center;
  font-size: 10.5px;
  color: var(--label-4);
  letter-spacing: 0;
}

@media (max-width: 520px) {
  .login-card {
    padding: 32px 24px 22px;
    border-radius: 26px;
  }
  h1 {
    font-size: 23px;
  }
}
</style>
