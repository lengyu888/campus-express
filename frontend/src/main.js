import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import { initMotion, vReveal } from './motion'
import './styles/index.css'

initMotion()

const app = createApp(App)
app.directive('reveal', vReveal)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.config.errorHandler = (error, instance, info) => {
  console.error('[app-error]', info, error)
  ElMessage.error('页面出现异常，请刷新后重试')
}

window.addEventListener('unhandledrejection', (event) => {
  console.error('[unhandled-rejection]', event.reason)
})

app.mount('#app')
