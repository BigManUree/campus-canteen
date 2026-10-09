<template>
  <div class="page-shell messages-page">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>消息中心</h3>
            <p>查看站内消息、标记已读、向指定用户发送新消息。</p>
          </div>
          <div class="toolbar-actions">
            <el-input-number v-model="targetUserId" :min="1" :controls="false" placeholder="查看指定用户 ID" style="width: 180px" @input="handleTargetUserInput" />
            <el-button :loading="loading" :disabled="loading" @click="loadData">加载用户消息</el-button>
            <el-button :disabled="loading" @click="switchToMyMessages">查看我的消息</el-button>
            <el-button :disabled="!unreadCount || markingAll || loading" :loading="markingAll" @click="markAllRead">全部已读</el-button>
            <el-button type="primary" :disabled="loading || submitting" @click="openCreate">发送消息</el-button>
          </div>
        </div>
      </template>

      <div class="message-summary">
        <div class="message-summary__card message-summary__card--hero">
          <span>消息总数</span>
          <strong>{{ filteredList.length }}</strong>
          <p>当前列表可见消息</p>
        </div>
        <div class="message-summary__card">
          <span>未读消息</span>
          <strong>{{ unreadCount }}</strong>
          <p>需要优先处理</p>
        </div>
        <div class="message-summary__card">
          <span>订单类</span>
          <strong>{{ orderMessageCount }}</strong>
          <p>与订单流程强相关</p>
        </div>
        <div class="message-summary__card">
          <span>系统类</span>
          <strong>{{ systemMessageCount }}</strong>
          <p>运营或后台通知</p>
        </div>
      </div>

      <div class="message-context">
        <div class="message-context__tags">
          <el-tag :type="targetUserId ? 'warning' : 'info'" round>
            {{ targetUserId ? `当前查看用户 ${targetUserId}` : '当前查看我的消息' }}
          </el-tag>
          <el-tag v-if="query.keyword" effect="dark" round>关键词：{{ query.keyword }}</el-tag>
          <el-tag v-if="query.readStatus !== undefined" type="success" round>{{ Number(query.readStatus) === 1 ? '仅看已读' : '仅看未读' }}</el-tag>
          <el-tag v-if="query.type !== undefined" type="warning" round>{{ Number(query.type) === 1 ? '订单消息' : '系统消息' }}</el-tag>
        </div>
        <el-button v-if="query.keyword || query.readStatus !== undefined || query.type !== undefined" link @click="resetFilters">清空筛选</el-button>
      </div>

      <el-table v-if="!hasFilterBarEmptyState" :data="filteredList" v-loading="loading" row-key="message_id" empty-text="当前没有消息，发送一条新消息试试。">
        <el-table-column prop="message_id" label="消息 ID" min-width="100" />
        <el-table-column label="类型" min-width="120">
          <template #default="{ row }">
            <el-tag :type="Number(row.type) === 1 ? 'warning' : 'info'">{{ Number(row.type) === 1 ? '订单消息' : '系统消息' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="内容" min-width="480" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="message-cell">
              <strong>{{ row.content || '-' }}</strong>
              <span>发送方 {{ row.from_user_id }} / 接收方 {{ row.to_user_id }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="关联订单" min-width="120">
          <template #default="{ row }">{{ row.order_id || '-' }}</template>
        </el-table-column>
        <el-table-column label="读取状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="Number(row.is_read) === 1 ? 'success' : 'danger'">{{ Number(row.is_read) === 1 ? '已读' : '未读' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发送时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="220">
          <template #default="{ row }">
            <el-space wrap>
              <el-button v-if="Number(row.is_read) !== 1" size="small" type="primary" plain :loading="markingId === row.message_id" :disabled="deletingId === row.message_id || markingAll" @click="markRead(row)">标记已读</el-button>
              <el-button size="small" :disabled="markingAll" @click="copyMessage(row)">复制</el-button>
              <el-button size="small" type="danger" plain :loading="deletingId === row.message_id" :disabled="markingAll || markingId === row.message_id" @click="removeMessage(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="没有匹配的消息，换个筛选条件试试。" class="messages-empty">
        <el-button @click="resetFilters">重置筛选</el-button>
      </el-empty>
    </el-card>

    <el-dialog v-model="dialogVisible" title="发送消息" width="520px" @closed="handleClosed">
      <el-form ref="formRef" label-width="96px" :model="form" :rules="rules">
        <el-form-item label="接收用户" prop="to_user_id">
          <el-input-number v-model="form.to_user_id" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="关联订单">
          <el-input-number v-model="form.order_id" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="消息类型" prop="type">
          <el-select v-model="form.type" style="width: 100%">
            <el-option label="订单消息" :value="1" />
            <el-option label="系统消息" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="submitting" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="submitDisabled" @click="submitForm">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { messageApi } from '@/api/modules/messages'
import { formatDateTime } from '@/utils/formatters'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const list = ref([])
const stats = ref({ unread_count: 0 })
const targetUserId = ref(null)
const deletingId = ref(null)
const markingId = ref(null)
const markingAll = ref(false)
const targetUserTimer = ref(null)
const query = reactive({ readStatus: undefined, type: undefined, keyword: '' })
const form = reactive({ to_user_id: null, order_id: null, content: '', type: 1 })

const rules = {
  to_user_id: [{ required: true, message: '请输入接收用户 ID', trigger: 'change' }],
  content: [{ required: true, message: '请输入消息内容', trigger: 'blur' }],
  type: [{ required: true, message: '请选择消息类型', trigger: 'change' }]
}

const filteredList = computed(() => list.value.filter((item) => {
  const readMatched = query.readStatus === undefined || Number(item.is_read) === Number(query.readStatus)
  const typeMatched = query.type === undefined || Number(item.type) === Number(query.type)
  const keywordMatched = !query.keyword || String(item.content || '').includes(query.keyword.trim())
  return readMatched && typeMatched && keywordMatched
}))
const unreadCount = computed(() => Number(stats.value?.unread_count ?? list.value.filter((item) => Number(item.is_read) !== 1).length))
const orderMessageCount = computed(() => filteredList.value.filter((item) => Number(item.type) === 1).length)
const systemMessageCount = computed(() => filteredList.value.filter((item) => Number(item.type) === 2).length)
const hasFilterBarEmptyState = computed(() => !loading.value && list.value.length > 0 && filteredList.value.length === 0)
const submitDisabled = computed(() => submitting.value || !String(form.content || '').trim() || !form.to_user_id)

const getTargetUserId = () => targetUserId.value || undefined
const clearTargetUserTimer = () => {
  if (targetUserTimer.value) {
    window.clearTimeout(targetUserTimer.value)
    targetUserTimer.value = null
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const [listResult, statResult] = await Promise.all([
      messageApi.getList({ user_id: getTargetUserId() }),
      messageApi.getUnreadCount({ user_id: getTargetUserId() }).catch(() => ({ unread_count: 0 }))
    ])
    list.value = Array.isArray(listResult) ? listResult : listResult?.items || listResult?.data || []
    stats.value = statResult || { unread_count: 0 }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载消息列表失败')
  } finally {
    loading.value = false
  }
}

const handleTargetUserInput = () => {
  clearTargetUserTimer()
  targetUserTimer.value = window.setTimeout(() => {
    loadData()
  }, 300)
}
const handleSearch = () => {
  query.keyword = query.keyword.trim()
}
const handleFilterChange = () => {
  query.keyword = query.keyword.trim()
}
const resetFilters = () => {
  query.readStatus = undefined
  query.type = undefined
  query.keyword = ''
}

const switchToMyMessages = async () => {
  clearTargetUserTimer()
  targetUserId.value = null
  resetFilters()
  await loadData()
}

const openCreate = () => {
  if (targetUserId.value && !form.to_user_id) {
    form.to_user_id = targetUserId.value
  }
  dialogVisible.value = true
}
const handleClosed = () => {
  formRef.value?.resetFields()
  formRef.value?.clearValidate()
  Object.assign(form, { to_user_id: null, order_id: null, content: '', type: 1 })
}

const submitForm = async () => {
  if (submitting.value) return
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请先完善消息内容后再发送')
    return
  }
  submitting.value = true
  try {
    await messageApi.send({ ...form, order_id: form.order_id || null, content: form.content.trim() })
    targetUserId.value = form.to_user_id
    ElMessage.success('消息已发送')
    dialogVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '发送消息失败')
  } finally {
    submitting.value = false
  }
}

const markRead = async (row) => {
  if (markingId.value || markingAll.value) return
  const backup = { ...row }
  const previousUnread = unreadCount.value
  markingId.value = row.message_id
  row.is_read = 1
  try {
    const result = await messageApi.markRead(row.message_id)
    row.is_read = Number(result?.data?.is_read ?? result?.is_read ?? 1)
    row.read_time = result?.data?.read_time || result?.read_time || row.read_time
    stats.value.unread_count = Math.max(0, previousUnread - 1)
    ElMessage.success('消息已标记为已读')
  } catch (error) {
    Object.assign(row, backup)
    stats.value.unread_count = previousUnread
    ElMessage.error(error?.response?.data?.detail || error?.message || '标记已读失败')
  } finally {
    markingId.value = null
  }
}

const markAllRead = async () => {
  if (markingAll.value) return
  const backups = list.value.map((item) => ({ ...item }))
  const previousUnread = unreadCount.value
  markingAll.value = true
  list.value = list.value.map((item) => ({ ...item, is_read: 1 }))
  stats.value.unread_count = 0
  try {
    await messageApi.markAllRead(getTargetUserId())
    ElMessage.success(previousUnread ? '全部消息已标记为已读' : '当前没有未读消息')
  } catch (error) {
    list.value = backups
    stats.value.unread_count = previousUnread
    ElMessage.error(error?.response?.data?.detail || error?.message || '批量标记已读失败')
  } finally {
    markingAll.value = false
  }
}

const copyMessage = async (row) => {
  const text = [`消息 ID：${row.message_id}`, `内容：${row.content || '-'}`, `订单：${row.order_id || '-'}`].join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('消息内容已复制')
  } catch (_error) {
    ElMessage.warning('当前环境不支持复制')
  }
}

const removeMessage = async (row) => {
  if (deletingId.value) return
  try {
    await ElMessageBox.confirm(`确认删除消息 ${row.message_id} 吗？`, '删除消息', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除消息')
    return
  }
  const backup = [...list.value]
  const previousUnread = unreadCount.value
  deletingId.value = row.message_id
  list.value = list.value.filter((item) => item.message_id !== row.message_id)
  if (Number(row.is_read) !== 1) {
    stats.value.unread_count = Math.max(0, previousUnread - 1)
  }
  try {
    await messageApi.remove(row.message_id)
    ElMessage.success('消息已删除')
  } catch (error) {
    list.value = backup
    stats.value.unread_count = previousUnread
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除消息失败')
  } finally {
    deletingId.value = null
  }
}

onMounted(loadData)
onBeforeUnmount(() => {
  clearTargetUserTimer()
})
</script>

<style scoped lang="scss">
.messages-page {
  display: grid;
  gap: 20px;
}

.message-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.message-summary__card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  background: rgba(255, 255, 255, 0.03);

  span,
  p {
    color: #8d98b5;
  }

  strong {
    display: block;
    margin: 10px 0 8px;
    font-size: 26px;
  }
}

.message-summary__card--hero strong {
  font-size: 34px;
}

.message-context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.message-context__tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.messages-empty {
  padding: 24px 0 6px;
}

.message-cell {
  display: grid;
  gap: 6px;

  span {
    color: #8d98b5;
    font-size: 13px;
  }
}
</style>

