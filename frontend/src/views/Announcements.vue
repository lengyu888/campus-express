<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>公告管理</h1>
        <p>{{ published }} 条已发布 · {{ offline }} 条已下架</p>
      </div>
      <div class="head-actions">
        <el-button round :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
        <el-button type="primary" round :icon="Plus" @click="openCreate">发布公告</el-button>
      </div>
    </header>

    <section v-if="!items.length && !loading" class="empty card" v-reveal>
      <div class="empty-icon"><el-icon :size="26"><Document /></el-icon></div>
      <h3>还没有公告</h3>
      <p>发布营业时间调整、超期提醒等通知，学生会在消息中心看到。</p>
      <el-button type="primary" round :icon="Plus" @click="openCreate">发布公告</el-button>
    </section>

    <section v-else class="grid">
      <article v-for="(item, i) in items" :key="item.id" class="announce card" v-reveal="i * 60">
        <div class="announce-head">
          <div>
            <h3>{{ item.title }}</h3>
            <span class="meta">
              {{ item.publisher_name || '系统' }} · {{ fmt(item.publish_at || item.created_at) }}
            </span>
          </div>
          <span class="pill" :class="item.status === 1 ? 'on' : 'off'">
            {{ item.status === 1 ? '已发布' : '已下架' }}
          </span>
        </div>

        <p class="content">{{ item.content }}</p>

        <div class="actions">
          <button class="link" type="button" @click="openEdit(item)">编辑</button>
          <button v-if="item.status === 1" class="link danger" type="button" @click="takeOff(item)">
            下架
          </button>
          <button v-else class="link" type="button" @click="republish(item)">重新发布</button>
        </div>
      </article>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑公告' : '发布公告'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="公告标题" prop="title">
          <el-input v-model="form.title" maxlength="100" placeholder="如：东区驿站营业时间调整" />
        </el-form-item>
        <el-form-item label="公告正文" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="6" maxlength="5000"
                    show-word-limit placeholder="面向全校师生发布的通知内容" />
        </el-form-item>
        <el-form-item label="发布状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">立即发布</el-radio>
            <el-radio :value="0">暂存下架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" round :loading="submitting" @click="submit">
          {{ editing ? '保存修改' : '发布' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Document } from '@element-plus/icons-vue'
import {
  createAnnouncement, deleteAnnouncement, listAnnouncements, updateAnnouncement
} from '../api/notifications'

const items = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const submitting = ref(false)
const formRef = ref()

const form = reactive({ title: '', content: '', status: 1 })

const rules = {
  title: [{ required: true, min: 2, message: '请填写公告标题', trigger: 'blur' }],
  content: [{ required: true, min: 2, message: '请填写公告正文', trigger: 'blur' }]
}

const published = computed(() => items.value.filter((i) => i.status === 1).length)
const offline = computed(() => items.value.filter((i) => i.status === 0).length)

function fmt(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function load() {
  loading.value = true
  try {
    const data = await listAnnouncements({ page: 1, page_size: 50, include_offline: true })
    items.value = data.items
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, { title: '', content: '', status: 1 })
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

function openEdit(item) {
  editing.value = item
  Object.assign(form, { title: item.title, content: item.content, status: item.status })
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editing.value) {
      await updateAnnouncement(editing.value.id, { ...form })
      ElMessage.success('公告已更新')
    } else {
      await createAnnouncement({ ...form })
      ElMessage.success('公告已发布')
    }
    dialogVisible.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

async function takeOff(item) {
  try {
    await ElMessageBox.confirm(`确认下架「${item.title}」吗？下架后学生将不可见。`, '下架公告', {
      confirmButtonText: '确认下架', cancelButtonText: '取消', type: 'warning'
    })
  } catch (e) {
    return
  }
  await deleteAnnouncement(item.id)
  ElMessage.success('公告已下架')
  await load()
}

async function republish(item) {
  await updateAnnouncement(item.id, { title: item.title, content: item.content, status: 1 })
  ElMessage.success('公告已重新发布')
  await load()
}

onMounted(load)
</script>

<style scoped>
.head-actions {
  display: flex;
  gap: 8px;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.announce {
  padding: 22px 24px 16px;
  display: flex;
  flex-direction: column;
}

.announce-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.announce h3 {
  margin: 0 0 4px;
  font-size: 14.5px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.meta {
  font-size: 11px;
  color: var(--label-3);
}

.pill {
  display: inline-flex;
  align-items: center;
  height: 21px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
  flex-shrink: 0;
}

.pill.on {
  background: rgba(52, 199, 89, 0.13);
  color: #1d7a37;
}

.pill.off {
  background: rgba(120, 120, 128, 0.13);
  color: var(--label-2);
}

.content {
  margin: 0 0 14px;
  font-size: 12.5px;
  color: var(--label-2);
  line-height: 1.75;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
  white-space: pre-wrap;
}

.actions {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--separator);
  margin-top: auto;
}

.link {
  border: none;
  background: transparent;
  color: var(--ios-blue);
  font-family: inherit;
  font-size: 12px;
  cursor: pointer;
  padding: 3px 2px;
}

.link.danger {
  color: var(--ios-red);
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

@media (max-width: 980px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
