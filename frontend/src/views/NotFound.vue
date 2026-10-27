<template>
  <div class="tip-page">
    <div class="glow"></div>
    <div class="tip-card">
      <div class="icon-wrap">
        <el-icon :size="30"><Compass /></el-icon>
      </div>
      <span class="code">404</span>
      <h1>页面不存在</h1>
      <p>你访问的页面可能已被移除，或者地址输入有误。</p>
      <el-button type="primary" round size="large" @click="$router.replace('/dashboard')">返回工作台</el-button>
    </div>
  </div>
</template>

<script setup>
import { Compass } from '@element-plus/icons-vue'
</script>

<style scoped>
.tip-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #f5f5f7;
}

.glow {
  position: absolute;
  width: 620px;
  height: 620px;
  border-radius: 50%;
  background: radial-gradient(circle at 40% 40%, rgba(175, 82, 222, 0.16), transparent 65%);
  filter: blur(30px);
  animation: float-slow 16s ease-in-out infinite;
}

.tip-card {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 48px 56px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(30px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 24px 70px rgba(31, 45, 61, 0.12);
  animation: rise 0.6s var(--ease-out) both;
}

.icon-wrap {
  width: 62px;
  height: 62px;
  margin: 0 auto 16px;
  border-radius: 19px;
  background: rgba(175, 82, 222, 0.1);
  color: var(--ios-purple);
  display: flex;
  align-items: center;
  justify-content: center;
}

.code {
  display: block;
  font-size: 12px;
  letter-spacing: 0.28em;
  color: var(--label-3);
  margin-bottom: 8px;
}

h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

p {
  margin: 0 0 24px;
  color: var(--label-2);
  font-size: 13px;
  line-height: 1.7;
}
</style>
