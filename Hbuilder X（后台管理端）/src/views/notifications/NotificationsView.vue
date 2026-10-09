<template>
  <div class="page-shell">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>通知中心</h3>
            <p>查看当前登录管理员收到的通知，支持筛选、详情查看、标记已读与删除。</p>
          </div>
          <div class="toolbar-actions">
            <el-select v-model="query.notification_type" clearable placeholder="通知类型" style="width: 160px" @change="handleSearch">
              <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="query.category" clearable placeholder="通知分类" style="width: 160px" @change="handleSearch">
              <el-option v-for="item in categoryOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="query.readStatus" clearable placeholder="读取状态" style="width: 160px" @change="handleSearch">
              <el-option label="未读" :value="0" />
              <el-option label="已读" :value="1" />
            </el-select>
            <el-button type="primary" :loading="loading" @click="loadData">刷新通知</el-button>
            <el-button :disabled="!unreadIds.length" @click="markAllRead">全部标记已读</el-button>
          </div>
        </div>
      </template>

      <div class="headline-strip">
        <div class="headline-card">
          <span>通知总数</span>
          <strong>{{ pagination.total }}</strong>
        </div>
        <div class="headline-card">
          <span>未读数量</span>
          <strong>{{ unreadCount }}</strong>
        </div>
        <div class="headline-card">
          <span>筛选结果</span>
          <strong>{{ list.length }}</strong>
        </div>
      </div>

      <el-table :data="list" v-loading="loading" row-key="notification_id">
        <el-table-column prop="notification_id" label="通知 ID" min-width="100" />
        <el-table-column label="类型" min-width="140">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ formatType(row.notification_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分类" min-width="140">
          <template #default="{ row }">
            <el-tag size="small" :type="row.category === 'refund' ? 'danger' : 'info'">{{ formatCategory(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="220">
          <template #default="{ row }">
            <div class="notification-title-cell">
              <strong>{{ row.title || '系统通知' }}</strong>
              <el-tag v-if="!isRead(row)" size="small" type="warning">未读</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="内容" min-width="420" show-overflow-tooltip />
        <el-table-column label="发送时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="220">
          <template #default="{ row }">
            <el-space wrap>
              <el-button size="small" @click="openDetail(row)">详情</el-button>
              <el-button v-if="!isRead(row)" size="small" type="primary" plain @click="markRead(row)">标记已读</el-button>
              <el-button size="small" type="danger" plain @click="removeNotification(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="query.pageNum"
          v-model:page-size="query.pageSize"
          background
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" size="520px" title="通知详情">
      <template v-if="currentNotification">
        <div class="detail-stack">
          <div class="detail-panel">
            <span>标题</span>
            <strong>{{ currentNotification.title || '系统通知' }}</strong>
          </div>
          <div class="detail-panel">
            <span>通知类型</span>
            <strong>{{ formatType(currentNotification.notification_type) }}</strong>
          </div>
          <div class="detail-panel">
            <span>通知分类</span>
            <strong>{{ formatCategory(currentNotification.category) }}</strong>
          </div>
          <div class="detail-panel detail-panel--content">
            <span>通知内容</span>
            <p>{{ currentNotification.message || '暂无内容' }}</p>
          </div>
          <div class="detail-panel">
            <span>发送时间</span>
            <strong>{{ formatDateTime(currentNotification.create_time) }}</strong>
          </div>
          <div class="detail-panel">
            <span>读取时间</span>
            <strong>{{ formatDateTime(currentNotification.read_time) }}</strong>
          </div>
          <div class="detail-panel">
            <span>业务关联</span>
            <strong>{{ currentNotification.related_id ? `关联 ID / ${currentNotification.related_id}` : '无' }}</strong>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { notificationApi } from '@/api/modules/notifications'
import { formatDateTime, normalizeListPayload } from '@/utils/formatters'

const loading = ref(false)
const list = ref([])
const currentNotification = ref(null)
const detailVisible = ref(false)
const pagination = reactive({ total: 0, totalPages: 0 })
const statistics = ref(null)
const query = reactive({
  pageNum: 1,
  pageSize: 10,
  notification_type: '',
  category: '',
  readStatus: undefined
})

const typeOptions = [
  { label: '普通', value: 'normal' },
  { label: '紧急', value: 'urgent' },
  { label: '营销', value: 'marketing' }
]

const categoryOptions = [
  { label: '订单', value: 'order' },
  { label: '退款', value: 'refund' },
  { label: '取餐', value: 'pickup' },
  { label: '推广', value: 'promotion' },
  { label: '系统', value: 'system' }
]

const formatType = (value) => ({ normal: '普通', urgent: '紧急', marketing: '营销' }[value] || value || '未分类')
const formatCategory = (value) => ({ order: '订单', refund: '退款', pickup: '取餐', promotion: '推广', system: '系统' }[value] || value || '未分类')
const isRead = (row) => row?.is_read === true
const unreadIds = computed(() => list.value.filter((item) => !isRead(item)).map((item) => item.notification_id))
const unreadCount = computed(() => Number(statistics.value?.unread ?? unreadIds.value.length))

const loadData = async () => {
  loading.value = true
  try {
    const [listResult, statisticsResult] = await Promise.all([
      notificationApi.getList({
        pageNum: query.pageNum,
        pageSize: query.pageSize,
        notification_type: query.notification_type || undefined,
        category: query.category || undefined,
        readStatus: query.readStatus
      }),
      notificationApi.getStatistics().catch(() => null)
    ])
    const normalized = normalizeListPayload(listResult)
    list.value = normalized.items
    pagination.total = normalized.total
    pagination.totalPages = normalized.totalPages
    statistics.value = statisticsResult?.data || statisticsResult || null
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载通知列表失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  query.pageNum = page
  loadData()
}

const handlePageSizeChange = (pageSize) => {
  query.pageNum = 1
  query.pageSize = pageSize
  loadData()
}

const handleSearch = () => {
  query.pageNum = 1
  loadData()
}

const markRead = async (row) => {
  try {
    await notificationApi.markRead({ notification_ids: [row.notification_id] })
    ElMessage.success('已标记为已读')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '标记通知已读失败')
  }
}

const markAllRead = async () => {
  try {
    await notificationApi.markRead({ notification_ids: null })
    ElMessage.success('全部未读通知已标记为已读')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '批量标记通知已读失败')
  }
}

const removeNotification = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除通知「${row.title || '系统通知'}」吗？`, '删除通知', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除通知')
    return
  }

  try {
    await notificationApi.remove(row.notification_id)
    ElMessage.success('通知已删除')
    if (detailVisible.value && String(currentNotification.value?.notification_id || '') === String(row.notification_id || '')) {
      detailVisible.value = false
    }
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除通知失败')
  }
}

const openDetail = (row) => {
  currentNotification.value = row
  detailVisible.value = true
  ElMessage.info('已打开通知详情')
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.toolbar,
.toolbar-actions,
.headline-strip {
  display: flex;
  gap: 12px;
}

.toolbar {
  align-items: center;
  justify-content: space-between;

  h3 {
    margin: 0;
    font-size: 22px;
  }

  p {
    margin: 8px 0 0;
    color: #8d98b5;
  }
}

.toolbar-actions {
  flex-wrap: wrap;
}

.headline-strip {
  margin-bottom: 18px;
}

.headline-card,
.detail-panel {
  padding: 14px 16px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
}

.headline-card {
  min-width: 180px;

  span {
    display: block;
    margin-bottom: 10px;
    color: #90a0c0;
  }

  strong {
    font-size: 24px;
  }
}

.notification-title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-stack {
  display: grid;
  gap: 14px;
}

.detail-panel {
  span {
    display: block;
    margin-bottom: 8px;
    color: #8d98b5;
    font-size: 13px;
  }

  p {
    margin: 0;
    line-height: 1.8;
    color: #c9d3eb;
  }
}

.pagination-wrap {
  margin-top: 22px;
}
</style>
