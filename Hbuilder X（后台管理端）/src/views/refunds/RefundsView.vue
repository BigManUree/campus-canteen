<template>
  <div class="page-shell">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>退款管理</h3>
            <p>审批退款申请，查看退款金额、原因与处理状态。</p>
          </div>
          <div class="toolbar-actions">
            <el-select v-model="query.refundStatus" clearable placeholder="退款状态" style="width: 180px" @change="handleFilterChange">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-input v-model="query.orderNo" clearable placeholder="订单号" style="width: 180px" @clear="handleFilterChange" @keyup.enter="handleSearch" />
            <el-input v-model="query.userId" clearable placeholder="用户 ID" style="width: 160px" @clear="handleFilterChange" @keyup.enter="handleSearch" />
            <el-date-picker
              v-model="dateRange"
              @change="handleFilterChange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 260px"
            />
            <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
            <el-button v-if="fromOrders" type="info" plain @click="backToOrders">回到订单</el-button>
          </div>
        </div>
      </template>

      <div class="stats-strip">
        <div class="stats-card">
          <span>总退款数</span>
          <strong>{{ pagination.total }}</strong>
        </div>
        <div class="stats-card">
          <span>待处理金额</span>
          <strong>¥{{ currency(pendingAmount) }}</strong>
        </div>
        <div class="stats-card">
          <span>已通过金额</span>
          <strong>¥{{ currency(approvedAmount) }}</strong>
        </div>
        <div class="stats-card">
          <span>已拒绝金额</span>
          <strong>¥{{ currency(rejectedAmount) }}</strong>
        </div>
      </div>

      <div class="status-distribution">
        <div v-for="item in distributionCards" :key="item.label" class="distribution-item">
          <div class="distribution-item__meta">
            <strong>{{ item.label }}</strong>
            <span>{{ item.value }}</span>
          </div>
          <div class="distribution-item__bar">
            <div class="distribution-item__fill" :style="{ width: `${item.percent}%`, background: item.gradient }"></div>
          </div>
        </div>
      </div>

      <div v-if="activeLinkLabel" class="refund-link-banner">
        <div>
          <strong>{{ activeLinkLabel }}</strong>
          <p>{{ activeLinkDescription }}</p>
        </div>
        <div class="refund-link-banner__actions">
          <el-button v-if="fromOrders" text @click="backToOrders">回到订单</el-button>
          <el-button text @click="clearLinkedFilter">清除联动</el-button>
        </div>
      </div>

      <div v-if="feedbackMessage" class="refund-feedback-banner" :class="`refund-feedback-banner--${feedbackType}`">
        <div>
          <strong>{{ feedbackTitle }}</strong>
          <p>{{ feedbackMessage }}</p>
        </div>
        <div class="refund-feedback-banner__actions">
          <el-button v-if="fromOrders" :type="feedbackType === 'success' ? 'success' : 'info'" plain @click="backToOrders">回到订单</el-button>
          <el-button text @click="dismissFeedback">知道了</el-button>
        </div>
      </div>

      <el-table :data="list" v-loading="loading" row-key="refund_id">
        <el-table-column prop="refund_id" label="退款 ID" min-width="100" />
        <el-table-column prop="order_no" label="订单编号" min-width="180" />
        <el-table-column label="申请用户" min-width="220">
          <template #default="{ row }">{{ pickText(row.user || row, ['nickname', 'username']) }} / {{ pickText(row.user || row, ['phone', 'user_phone']) }}</template>
        </el-table-column>
        <el-table-column label="档口信息" min-width="180">
          <template #default="{ row }">{{ pickText(row.stall || row.canteen || row, ['stall_name', 'canteen_name', 'name']) }}</template>
        </el-table-column>
        <el-table-column label="退款金额" min-width="120">
          <template #default="{ row }">¥{{ currency(row.refund_amount) }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="退款原因" min-width="220" show-overflow-tooltip />
        <el-table-column label="审批备注" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ pickText(row, ['admin_remark', 'remark', 'reject_reason', 'approval_remark']) }}</template>
        </el-table-column>
        <el-table-column label="状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.refund_status ?? row.status)">{{ statusText(row.refund_status ?? row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.create_time || row.apply_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="300">
          <template #default="{ row }">
            <el-space wrap>
              <el-button size="small" @click="openDetail(row)">详情</el-button>
              <el-button size="small" @click="copyRefundSummary(row)">复制信息</el-button>
              <el-button v-if="normalizeRefundStatus(row) === 'pending'" type="success" size="small" @click="approve(row)">批准</el-button>
              <el-button v-if="normalizeRefundStatus(row) === 'pending'" type="danger" size="small" plain @click="reject(row)">拒绝</el-button>
              <el-tag v-else :type="statusType(row.refund_status ?? row.status)">{{ statusText(row.refund_status ?? row.status) }}</el-tag>
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

    <el-drawer v-model="detailVisible" size="560px" title="退款详情">
      <template v-if="currentRefund">
        <div class="detail-grid">
          <div class="detail-item"><span>退款单号</span><strong>#{{ currentRefund.refund_id }}</strong></div>
          <div class="detail-item"><span>订单编号</span><strong>{{ currentRefund.order_no || currentRefund.order_id || '-' }}</strong></div>
          <div class="detail-item"><span>申请用户</span><strong>{{ pickText(currentRefund.user || currentRefund, ['nickname', 'username']) || '-' }}</strong></div>
          <div class="detail-item"><span>联系电话</span><strong>{{ pickText(currentRefund.user || currentRefund, ['phone', 'user_phone']) || '-' }}</strong></div>
          <div class="detail-item"><span>档口信息</span><strong>{{ pickText(currentRefund.stall || currentRefund.canteen || currentRefund, ['stall_name', 'canteen_name', 'name']) || '-' }}</strong></div>
          <div class="detail-item"><span>退款金额</span><strong>¥{{ currency(currentRefund.refund_amount) }}</strong></div>
          <div class="detail-item"><span>订单金额</span><strong>¥{{ currency(currentRefund.order_amount || currentRefund.total_amount) }}</strong></div>
          <div class="detail-item"><span>处理状态</span><strong>{{ statusText(currentRefund.refund_status ?? currentRefund.status) }}</strong></div>
          <div class="detail-item"><span>订单状态</span><strong>{{ currentRefund.order_status ?? '-' }}</strong></div>
          <div class="detail-item"><span>支付状态</span><strong>{{ currentRefund.payment_status ?? currentRefund.pay_status ?? '-' }}</strong></div>
          <div class="detail-item"><span>申请时间</span><strong>{{ formatDateTime(currentRefund.create_time || currentRefund.apply_time) }}</strong></div>
          <div class="detail-item"><span>审核时间</span><strong>{{ formatDateTime(currentRefund.audit_time || currentRefund.review_time) }}</strong></div>
        </div>

        <el-divider content-position="left">退款原因</el-divider>
        <div class="reason-panel">{{ currentRefund.reason || currentRefund.refund_reason || '未填写退款原因' }}</div>

        <el-divider content-position="left">审批备注</el-divider>
        <div class="reason-panel">{{ currentRefund.admin_remark || currentRefund.remark || currentRefund.reject_reason || currentRefund.approval_remark || '暂无审批备注' }}</div>

        <div v-if="normalizeRefundStatus(currentRefund) === 'pending'" class="detail-actions">
          <el-button type="success" @click="approve(currentRefund)">批准退款</el-button>
          <el-button type="danger" plain @click="reject(currentRefund)">拒绝退款</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { refundApi } from '@/api/modules/refunds'
import { currency, formatDateTime, normalizeListPayload, pickText } from '@/utils/formatters'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const list = ref([])
const currentRefund = ref(null)
const detailVisible = ref(false)
const pagination = reactive({ total: 0, totalPages: 0 })
const feedbackMessage = ref('')
const feedbackType = ref('success')
const dateRange = ref([])
const query = reactive({
  pageNum: 1,
  pageSize: 10,
  refundStatus: undefined,
  orderNo: '',
  userId: '',
  startTime: '',
  endTime: ''
})

const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '已批准', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
  { label: '已完成', value: 'completed' }
]

const normalizeRefundStatus = (row) => {
  const status = row?.refund_status ?? row?.status
  const normalized = typeof status === 'string' ? status.toLowerCase() : status
  const map = {
    0: 'pending',
    1: 'approved',
    2: 'rejected',
    3: 'completed',
    '0': 'pending',
    '1': 'approved',
    '2': 'rejected',
    '3': 'completed'
  }
  return map[normalized] || normalized || 'pending'
}

const statusText = (status) => ({ pending: '待处理', approved: '已批准', rejected: '已拒绝', completed: '已完成' }[normalizeRefundStatus({ status })] || '未知')
const statusType = (status) => ({ pending: 'warning', approved: 'success', rejected: 'danger', completed: 'info' }[normalizeRefundStatus({ status })] || 'info')

const fromOrders = computed(() => route.query.from === 'orders')
const linkedOrderText = computed(() => query.orderNo || query.userId || '当前筛选')
const feedbackTitle = computed(() => (feedbackType.value === 'success' ? '退款闭环已更新' : '当前订单退款状态已变化'))

const pendingAmount = computed(() => list.value.filter((item) => normalizeRefundStatus(item) === 'pending').reduce((sum, item) => sum + Number(item.refund_amount || 0), 0))
const approvedAmount = computed(() => list.value.filter((item) => normalizeRefundStatus(item) === 'approved').reduce((sum, item) => sum + Number(item.refund_amount || 0), 0))
const rejectedAmount = computed(() => list.value.filter((item) => normalizeRefundStatus(item) === 'rejected').reduce((sum, item) => sum + Number(item.refund_amount || 0), 0))

const distributionCards = computed(() => {
  const total = Math.max(Number(pagination.total || 0), 1)
  const pendingCount = list.value.filter((item) => normalizeRefundStatus(item) === 'pending').length
  const approvedCount = list.value.filter((item) => normalizeRefundStatus(item) === 'approved').length
  const rejectedCount = list.value.filter((item) => normalizeRefundStatus(item) === 'rejected').length

  return [
    { label: '待处理', value: pendingCount, percent: Math.round((pendingCount / total) * 100), gradient: 'linear-gradient(90deg, #ffb84d, #ff7a59)' },
    { label: '已批准', value: approvedCount, percent: Math.round((approvedCount / total) * 100), gradient: 'linear-gradient(90deg, #24c99a, #6ea8fe)' },
    { label: '已拒绝', value: rejectedCount, percent: Math.round((rejectedCount / total) * 100), gradient: 'linear-gradient(90deg, #ff6b81, #ff9f6e)' }
  ]
})

const activeLinkLabel = computed(() => {
  if (query.orderNo) return `已联动订单 ${query.orderNo}`
  if (query.userId) return `已联动用户 ${query.userId}`
  return ''
})

const activeLinkDescription = computed(() => {
  if (query.orderNo && query.refundStatus !== undefined) {
    return `当前筛选状态：${statusText(query.refundStatus)}，可直接完成退款审批闭环。`
  }
  if (query.orderNo) return '来自订单管理页的联动筛选，方便快速查看该订单的退款记录。'
  if (query.userId) return '当前已按申请用户联动筛选退款记录。'
  return ''
})

const syncDateRange = () => {
  query.startTime = dateRange.value?.[0] || ''
  query.endTime = dateRange.value?.[1] || ''
}

const syncRouteQuery = () => {
  query.orderNo = String(route.query.orderNo || '')
  query.userId = String(route.query.userId || '')
  query.refundStatus = route.query.status === undefined ? undefined : String(route.query.status)
}

const getPendingCountForCurrentOrder = () => {
  if (!query.orderNo) return 0
  return list.value.filter((item) => String(item.order_no || '') === String(query.orderNo) && normalizeRefundStatus(item) === 'pending').length
}

const loadData = async () => {
  loading.value = true
  try {
    syncDateRange()
    const listResult = await refundApi.getList({
      pageNum: query.pageNum,
      pageSize: query.pageSize,
      refundStatus: query.refundStatus,
      orderNo: query.orderNo || undefined,
      userId: query.userId || undefined,
      startTime: query.startTime || undefined,
      endTime: query.endTime || undefined
    })
    const normalized = normalizeListPayload(listResult)
    list.value = normalized.items
    pagination.total = normalized.total
    pagination.totalPages = normalized.totalPages
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载退款列表失败')
  } finally {
    loading.value = false
  }
}

const updateRouteQuery = (extra = {}) => {
  const nextQuery = {
    ...route.query,
    ...(query.orderNo ? { orderNo: query.orderNo } : { orderNo: undefined }),
    ...(query.userId ? { userId: query.userId } : { userId: undefined }),
    ...(query.refundStatus !== undefined ? { status: query.refundStatus } : { status: undefined }),
    ...extra
  }
  router.replace({ path: route.path, query: nextQuery })
}

const dismissFeedback = () => {
  feedbackMessage.value = ''
}

const backToOrders = () => {
  router.push({
    path: '/orders',
    query: {
      highlight_order_id: route.query.order_id || undefined,
      highlight_message: feedbackMessage.value || `订单 ${linkedOrderText.value} 已完成退款审批。`
    }
  })
}

const handleFilterChange = () => {
  query.pageNum = 1
  dismissFeedback()
  updateRouteQuery({ page: undefined })
  loadData()
}

const handlePageChange = (page) => {
  query.pageNum = page
  dismissFeedback()
  loadData()
}

const handlePageSizeChange = (pageSize) => {
  query.pageNum = 1
  query.pageSize = pageSize
  dismissFeedback()
  loadData()
}

const handleSearch = () => {
  query.pageNum = 1
  dismissFeedback()
  updateRouteQuery({ page: undefined })
  loadData()
}

const resetFilters = () => {
  query.pageNum = 1
  query.pageSize = 10
  query.refundStatus = undefined
  query.orderNo = ''
  query.userId = ''
  query.startTime = ''
  query.endTime = ''
  dateRange.value = []
  dismissFeedback()
  updateRouteQuery({ orderNo: undefined, userId: undefined, status: undefined, page: undefined, from: undefined, order_id: undefined })
  loadData()
}

const clearLinkedFilter = () => {
  resetFilters()
}

const openDetail = async (row) => {
  detailVisible.value = true
  currentRefund.value = row
  try {
    const detail = await refundApi.getDetail(row.refund_id)
    currentRefund.value = detail?.data || detail || row
  } catch (error) {
    ElMessage.warning(error?.response?.data?.detail || error?.message || '退款详情加载失败，已展示列表信息')
  }
}

const applyPostDecisionFeedback = async (actionText) => {
  await loadData()
  if (!fromOrders.value || !query.orderNo) return

  const pendingCount = getPendingCountForCurrentOrder()
  if (pendingCount === 0) {
    feedbackType.value = 'success'
    feedbackMessage.value = `订单 ${linkedOrderText.value} 已${actionText}，当前订单已无待处理退款，可返回订单页继续处理。`
    if (query.refundStatus === 'pending') {
      query.refundStatus = undefined
      updateRouteQuery({ status: undefined })
      await loadData()
    }
    return
  }

  feedbackType.value = 'info'
  feedbackMessage.value = `订单 ${linkedOrderText.value} 已${actionText}，仍有 ${pendingCount} 条待处理退款，已保留当前联动筛选。`
}

const auditRefund = async (row, action) => {
  const isApprove = action === 'approve'
  const result = await ElMessageBox.prompt(isApprove ? '请输入审批备注（可选）' : '请输入拒绝原因', isApprove ? '批准退款' : '拒绝退款', {
    confirmButtonText: isApprove ? '确认批准' : '确认拒绝',
    cancelButtonText: '返回',
    inputPlaceholder: isApprove ? '例如：订单异常已核实，同意退款' : '请输入拒绝原因'
  }).catch(() => null)
  if (result === null) {
    ElMessage.info('已取消退款审批操作')
    return
  }
  if (!isApprove && !result?.value) {
    ElMessage.warning('请输入拒绝原因后再提交')
    return
  }

  try {
    await refundApi.audit(row.refund_id, {
      action,
      admin_remark: result?.value || ''
    })
    ElMessage.success(isApprove ? '已批准退款' : '已拒绝退款申请')
    detailVisible.value = false
    await applyPostDecisionFeedback(isApprove ? '批准退款' : '完成退款审批')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || (isApprove ? '批准退款失败' : '拒绝退款失败'))
  }
}

const approve = async (row) => {
  await auditRefund(row, 'approve')
}

const reject = async (row) => {
  await auditRefund(row, 'reject')
}

const copyRefundSummary = async (row) => {
  const summary = [
    `退款单号：${row.refund_id || '-'}`,
    `订单编号：${row.order_no || row.order_id || '-'}`,
    `申请用户：${pickText(row.user || row, ['nickname', 'username'])}`,
    `退款金额：¥${currency(row.refund_amount)}`,
    `状态：${statusText(row.refund_status ?? row.status)}`,
    `原因：${row.reason || row.refund_reason || '未填写退款原因'}`
  ].join('\n')

  try {
    await navigator.clipboard.writeText(summary)
    ElMessage.success('退款摘要已复制')
  } catch (_error) {
    ElMessage.warning('当前环境不支持复制，请手动复制详情内容')
  }
}

watch(
  () => route.query,
  () => {
    syncRouteQuery()
    dismissFeedback()
    loadData()
  }
)

onMounted(() => {
  syncRouteQuery()
  loadData()
})
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;

  h3 {
    margin: 0;
    font-size: 22px;
  }

  p {
    margin: 8px 0 0;
    color: #8d98b5;
  }
}

.toolbar-actions,
.stats-strip,
.refund-link-banner__actions,
.refund-feedback-banner__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.stats-strip,
.status-distribution {
  margin-bottom: 18px;
}

.stats-card,
.detail-item,
.reason-panel,
.distribution-item,
.refund-link-banner,
.refund-feedback-banner {
  padding: 14px 16px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
}

.stats-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.stats-card span,
.detail-item span {
  display: block;
  margin-bottom: 8px;
  color: #8d98b5;
  font-size: 13px;
}

.stats-card strong {
  font-size: 24px;
}

.status-distribution {
  display: grid;
  gap: 12px;
}

.distribution-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.distribution-item__bar {
  height: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.distribution-item__fill {
  height: 100%;
  border-radius: inherit;
}

.refund-link-banner,
.refund-feedback-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.refund-link-banner p,
.refund-feedback-banner p {
  margin: 8px 0 0;
  color: #90a0c0;
}

.refund-feedback-banner--success {
  border-color: rgba(36, 201, 154, 0.25);
  background: rgba(36, 201, 154, 0.08);
}

.refund-feedback-banner--info {
  border-color: rgba(110, 168, 254, 0.25);
  background: rgba(110, 168, 254, 0.08);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.reason-panel {
  line-height: 1.8;
  color: #c9d3eb;
}

.detail-actions,
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.detail-actions {
  margin-top: 18px;
}

.pagination-wrap {
  margin-top: 22px;
}
</style>
