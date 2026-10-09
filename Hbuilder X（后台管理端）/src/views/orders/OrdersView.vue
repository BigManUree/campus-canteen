<template>
  <div class="page-shell page-grid">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>订单管理</h3>
            <p>查看订单详情、处理接单、完成制作与核销取餐。</p>
          </div>
          <div class="toolbar-actions">
            <el-select v-model="query.status" clearable placeholder="订单状态" style="width: 160px" @change="handleSearch">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="query.paymentStatus" clearable placeholder="支付状态" style="width: 160px" @change="handleSearch">
              <el-option label="待支付" :value="0" />
              <el-option label="已支付" :value="1" />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              @change="handleSearch"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 260px"
            />
            <el-input v-model="query.orderNo" clearable placeholder="订单号" style="width: 220px" @clear="handleSearch" @keyup.enter="handleSearch" />
            <el-button type="primary" @click="handleSearch" :loading="loading">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
            <el-button @click="handleExport">导出当前结果</el-button>
          </div>
        </div>
      </template>

      <div class="summary-grid">
        <div class="summary-stat summary-stat--accent">
          <span>筛选结果</span>
          <strong>{{ pagination.total }}</strong>
          <p>当前筛选条件下的订单数量</p>
        </div>
        <div v-for="item in summaryCards" :key="item.label" class="summary-stat">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.tip }}</p>
        </div>
      </div>

      <div v-if="highlightMessage" class="return-highlight-banner">
        <div>
          <strong>已返回订单页</strong>
          <p>{{ highlightMessage }}</p>
        </div>
        <el-button text @click="clearHighlightState">收起提示</el-button>
      </div>

      <div class="batch-bar">
        <div class="batch-bar__info">已选 {{ multipleSelection.length }} 项</div>
        <div class="batch-bar__actions">
          <el-button :disabled="!canBatchAccept" @click="handleBatchAccept">批量接单</el-button>
          <el-button type="success" plain :disabled="!canBatchComplete" @click="handleBatchComplete">批量制作完成</el-button>
          <el-button :disabled="!multipleSelection.length" @click="clearSelection">清空选择</el-button>
        </div>
      </div>

      <el-table ref="tableRef" :data="list" v-loading="loading" row-key="order_id" :row-class-name="getRowClassName" @selection-change="multipleSelection = $event">
        <el-table-column type="selection" width="54" />
        <el-table-column prop="order_no" label="订单号" min-width="220">
          <template #default="{ row }">
            <div class="order-no-cell">
              <span>{{ row.order_no }}</span>
              <el-tag v-if="String(row.order_id || '') === String(highlightOrderId || '')" size="small" type="warning" effect="dark">刚处理完成</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="用户" min-width="180">
          <template #default="{ row }">
            {{ getOrderUserText(row) }}
          </template>
        </el-table-column>
        <el-table-column label="档口" min-width="180">
          <template #default="{ row }">
            {{ getOrderStallText(row) }}
          </template>
        </el-table-column>
        <el-table-column label="订单金额" min-width="120">
          <template #default="{ row }">¥{{ currency(pickAmount(row, ['pay_amount', 'total_amount', 'order_amount'])) }}</template>
        </el-table-column>
        <el-table-column label="退款状态" min-width="180">
          <template #default="{ row }">
            <div class="refund-cell">
              <el-tag :type="refundTagType(getRefundStatus(row))" effect="dark">{{ refundStatusText(row) }}</el-tag>
              <span v-if="hasRefundRequest(row)" class="refund-cell__amount">¥{{ currency(getRefundAmount(row)) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="支付状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="Number(row.pay_status) === 1 ? 'success' : 'warning'">{{ Number(row.pay_status) === 1 ? '已支付' : '待支付' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="订单状态" min-width="130">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.order_status)">{{ statusText(row.order_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.create_time || row.order_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="360">
          <template #default="{ row }">
            <el-space wrap>
              <el-button size="small" @click="openDetail(row)">详情</el-button>
              <el-button size="small" @click="printReceipt(row)">打印小票</el-button>
              <el-button size="small" :type="hasPendingRefund(row) ? 'danger' : 'info'" :plain="!hasPendingRefund(row)" @click="goToRefund(row)">
                {{ hasPendingRefund(row) ? '处理退款' : '查看退款' }}
              </el-button>
              <el-button v-if="Number(row.order_status) === 0" size="small" type="primary" @click="acceptOrder(row)">接单</el-button>
              <el-button v-if="Number(row.order_status) === 1" size="small" type="success" @click="completeOrder(row)">制作完成</el-button>
              <el-button v-if="Number(row.order_status) === 2 && row.pickup_code" size="small" type="warning" plain @click="verifyPickup(row)">核销取餐</el-button>
              <el-button v-if="[0, 1].includes(Number(row.order_status))" size="small" type="danger" plain @click="cancelOrder(row)">取消订单</el-button>
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

    <el-drawer v-model="detailVisible" size="580px" title="订单详情">
      <template v-if="currentOrder">
        <div class="detail-grid">
          <div class="detail-item"><span>订单号</span><strong>{{ currentOrder.order_no || '-' }}</strong></div>
          <div class="detail-item"><span>用户</span><strong>{{ getOrderUserText(currentOrder) }}</strong></div>
          <div class="detail-item"><span>档口</span><strong>{{ getOrderStallText(currentOrder) }}</strong></div>
          <div class="detail-item"><span>取餐码</span><strong>{{ currentOrder.pickup_code || '-' }}</strong></div>
          <div class="detail-item"><span>状态</span><strong>{{ statusText(currentOrder.order_status) }}</strong></div>
          <div class="detail-item"><span>金额</span><strong>¥{{ currency(pickAmount(currentOrder, ['pay_amount', 'total_amount', 'order_amount'])) }}</strong></div>
          <div class="detail-item"><span>退款状态</span><strong>{{ refundStatusText(currentOrder) }}</strong></div>
          <div class="detail-item"><span>退款金额</span><strong>{{ hasRefundRequest(currentOrder) ? `¥${currency(getRefundAmount(currentOrder))}` : '—' }}</strong></div>
        </div>

        <div v-if="hasRefundRequest(currentOrder)" class="refund-highlight-card">
          <div>
            <strong>{{ hasPendingRefund(currentOrder) ? '该订单存在待处理退款' : '该订单已有退款记录' }}</strong>
            <p>{{ refundReasonText(currentOrder) }}</p>
          </div>
          <el-button :type="hasPendingRefund(currentOrder) ? 'danger' : 'primary'" @click="goToRefund(currentOrder)">
            {{ hasPendingRefund(currentOrder) ? '立即处理退款' : '查看退款记录' }}
          </el-button>
        </div>

        <el-divider content-position="left">菜品明细</el-divider>
        <el-timeline>
          <el-timeline-item v-for="(item, index) in getOrderItems(currentOrder)" :key="item.item_id || `${item.dish_id || 'item'}-${index}`" placement="top">
            <strong>{{ item.dish_name || item.name || '未命名菜品' }}</strong>
            <p>数量：{{ item.quantity || 0 }}，单价：¥{{ currency(item.price || item.unit_price || 0) }}</p>
            <p v-if="item.remark">备注：{{ item.remark }}</p>
          </el-timeline-item>
          <el-empty v-if="!getOrderItems(currentOrder).length" description="暂无菜品明细" />
        </el-timeline>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { orderApi } from '@/api/modules/orders'
import { currency, formatDateTime, normalizeListPayload, pickAmount, pickText } from '@/utils/formatters'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const list = ref([])
const currentOrder = ref(null)
const detailVisible = ref(false)
const statistics = ref({})
const multipleSelection = ref([])
const dateRange = ref([])
const tableRef = ref()
const pagination = reactive({ total: 0, totalPages: 0 })
const highlightOrderId = ref('')
const highlightMessage = ref('')
let highlightTimer = null

const query = reactive({
  pageNum: 1,
  pageSize: 10,
  status: undefined,
  paymentStatus: undefined,
  orderNo: '',
  startTime: '',
  endTime: ''
})

const statusOptions = [
  { label: '待确认', value: 0 },
  { label: '制作中', value: 1 },
  { label: '待取餐', value: 2 },
  { label: '配送中', value: 3 },
  { label: '已完成', value: 4 },
  { label: '已取消', value: 5 }
]

const refundStatusOptions = [
  { label: '无退款', value: 'none' },
  { label: '待处理', value: 'pending' },
  { label: '已批准', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
  { label: '已完成', value: 'completed' }
]

const statusCounter = computed(() => list.value.reduce((acc, item) => {
  const key = Number(item.order_status)
  acc[key] = (acc[key] || 0) + 1
  return acc
}, {}))

const refundCounter = computed(() => list.value.reduce((acc, item) => {
  const status = getRefundStatus(item)
  acc[status] = (acc[status] || 0) + 1
  return acc
}, {}))

const summaryCards = computed(() => {
  const statsData = statistics.value || {}
  const todaySales = pickAmount(statsData, ['todaySalesAmount', 'today_sales'], 0)
  const pendingOrders = Number(statsData.pendingOrderCount ?? statsData.pending_orders ?? 0)
  const pendingRefunds = Number(statsData.pendingRefundCount ?? 0)

  return [
    { label: '待确认', value: statusCounter.value[0] || 0, tip: '等待商家接单' },
    { label: '制作中', value: statusCounter.value[1] || 0, tip: '正在处理中的订单' },
    { label: '待退款处理', value: pendingRefunds || refundCounter.value.pending || 0, tip: '需要优先跟进的退款申请' },
    { label: '已完成', value: statusCounter.value[4] || 0, tip: '已完成履约的订单' },
    { label: '今日销售额', value: `¥${currency(todaySales)}`, tip: `看板待处理订单：${pendingOrders}` }
  ]
})

const canBatchAccept = computed(() => multipleSelection.value.length > 0 && multipleSelection.value.every((item) => Number(item.order_status) === 0))
const canBatchComplete = computed(() => multipleSelection.value.length > 0 && multipleSelection.value.every((item) => Number(item.order_status) === 1))

const statusText = (status) => statusOptions.find((item) => item.value === Number(status))?.label || '未知状态'
const statusTagType = (status) => ({ 0: 'warning', 1: 'primary', 2: 'success', 3: 'info', 4: 'success', 5: 'danger' }[Number(status)] || 'info')
const refundTagType = (status) => ({ none: 'info', pending: 'danger', approved: 'success', rejected: 'warning', completed: 'success' }[status] || 'info')

const getOrderUserText = (row) => pickText(row?.user || row, ['nickname', 'username', 'user_name', 'user_phone', 'phone'])
const getOrderStallText = (row) => pickText(row?.stall || row?.canteen || row, ['stall_name', 'canteen_name', 'name', 'window_no'])
const getOrderItems = (row) => Array.isArray(row?.items) ? row.items : (Array.isArray(row?.order_items) ? row.order_items : [])

const getRefundStatus = (row) => {
  const status = row?.refund_status ?? row?.latest_refund_status ?? row?.refund?.status
  if (status === 'pending' || status === 'approved' || status === 'rejected' || status === 'completed') {
    return status
  }
  if (status === 0 || status === '0') return 'pending'
  if (status === 1 || status === '1') return 'approved'
  if (status === 2 || status === '2') return 'rejected'
  if (status === 3 || status === '3') return 'completed'
  return hasRefundRequest(row) ? 'pending' : 'none'
}

const hasRefundRequest = (row) => Boolean(
  row?.refund_id ||
  row?.latest_refund_id ||
  row?.refund_reason ||
  row?.refund?.refund_id ||
  row?.refund?.status ||
  Number(row?.refund_amount || row?.refund?.refund_amount || 0) > 0
)

const hasPendingRefund = (row) => getRefundStatus(row) === 'pending'
const getRefundAmount = (row) => pickAmount(row, ['refund_amount']) || pickAmount(row?.refund || {}, ['refund_amount'])
const refundReasonText = (row) => row?.refund_reason || row?.refund?.reason || '用户已提交退款申请，请前往退款页处理。'
const refundStatusText = (row) => refundStatusOptions.find((item) => item.value === getRefundStatus(row))?.label || '退款处理中'

const syncDateRange = () => {
  query.startTime = dateRange.value?.[0] || ''
  query.endTime = dateRange.value?.[1] || ''
}

const clearHighlightState = () => {
  highlightOrderId.value = ''
  highlightMessage.value = ''
  if (highlightTimer) {
    window.clearTimeout(highlightTimer)
    highlightTimer = null
  }
  if (route.query.highlight_order_id || route.query.highlight_message) {
    router.replace({
      path: route.path,
      query: {
        ...route.query,
        highlight_order_id: undefined,
        highlight_message: undefined
      }
    })
  }
}

const getRowClassName = ({ row }) => String(row.order_id || '') === String(highlightOrderId.value || '') ? 'order-row-highlight' : ''

const tryActivateHighlight = async () => {
  const targetId = String(route.query.highlight_order_id || '')
  const targetMessage = String(route.query.highlight_message || '')
  if (!targetId) return

  highlightOrderId.value = targetId
  highlightMessage.value = targetMessage || `订单 ${targetId} 已完成退款审批，已为你高亮显示。`

  await nextTick()
  const matchedRow = list.value.find((item) => String(item.order_id || '') === targetId)
  if (matchedRow) {
    openDetail(matchedRow, { silent: true })
  }

  const rowElement = document.querySelector('.el-table .order-row-highlight')
  rowElement?.scrollIntoView({ behavior: 'smooth', block: 'center' })

  if (highlightTimer) {
    window.clearTimeout(highlightTimer)
  }
  highlightTimer = window.setTimeout(() => {
    clearHighlightState()
  }, 6000)
}

const loadData = async () => {
  loading.value = true
  try {
    syncDateRange()
    const [result, statisticsResult] = await Promise.all([
      orderApi.getList({
        pageNum: query.pageNum,
        pageSize: query.pageSize,
        orderNo: query.orderNo || undefined,
        status: query.status,
        paymentStatus: query.paymentStatus,
        startTime: query.startTime ? `${query.startTime}T00:00:00` : undefined,
        endTime: query.endTime ? `${query.endTime}T23:59:59` : undefined
      }),
      orderApi.getStatistics().catch(() => null)
    ])
    const normalized = normalizeListPayload(result)
    list.value = normalized.items
    pagination.total = normalized.total
    pagination.totalPages = normalized.totalPages
    statistics.value = statisticsResult?.data || statisticsResult || {}
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载订单列表失败')
  } finally {
    loading.value = false
  }

  await tryActivateHighlight()
}

const handleSearch = () => {
  query.pageNum = 1
  clearHighlightState()
  loadData()
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

const resetFilters = () => {
  query.pageNum = 1
  query.pageSize = 10
  query.status = undefined
  query.paymentStatus = undefined
  query.orderNo = ''
  query.startTime = ''
  query.endTime = ''
  dateRange.value = []
  clearHighlightState()
  loadData()
}

const openDetail = async (row, options = {}) => {
  detailVisible.value = true
  currentOrder.value = row
  try {
    const detail = await orderApi.getDetail(row.order_id)
    currentOrder.value = {
      ...row,
      ...detail
    }
    if (!options.silent) {
      ElMessage.success(`已打开订单 ${row.order_no || row.order_id} 详情`)
    }
  } catch (_error) {
  }
}

const updateOrderStatus = async (row, orderStatus, successMessage) => {
  try {
    await orderApi.updateStatus(row.order_id, { order_status: orderStatus })
    ElMessage.success(successMessage)
    if (detailVisible.value && String(currentOrder.value?.order_id || '') === String(row.order_id || '')) {
      currentOrder.value = {
        ...currentOrder.value,
        order_status: orderStatus
      }
    }
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '更新订单状态失败')
  }
}

const acceptOrder = async (row) => {
  await updateOrderStatus(row, 1, '接单成功')
}

const completeOrder = async (row) => {
  await updateOrderStatus(row, 2, '已更新为待取餐')
}

const cancelOrder = async (row) => {
  const result = await ElMessageBox.prompt('请输入取消原因', '取消订单', {
    confirmButtonText: '确认取消',
    cancelButtonText: '返回',
    inputValue: '自动化测试取消',
    inputPlaceholder: '请输入取消原因'
  }).catch(() => null)
  if (!result?.value) {
    ElMessage.info('已取消操作')
    return
  }
  try {
    await orderApi.cancel(row.order_id, { reason: result.value })
    ElMessage.success('订单已取消')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '取消订单失败')
  }
}

const verifyPickup = async (row) => {
  const result = await ElMessageBox.prompt('请输入取餐码', '核销取餐', {
    confirmButtonText: '确认核销',
    cancelButtonText: '返回',
    inputValue: row.pickup_code || ''
  }).catch(() => null)
  if (!result?.value) {
    ElMessage.info('已取消核销')
    return
  }
  try {
    await orderApi.verifyPickup(row.order_id, { pickup_code: result.value })
    ElMessage.success('取餐码核销成功')
    if (detailVisible.value && String(currentOrder.value?.order_id || '') === String(row.order_id || '')) {
      currentOrder.value = {
        ...currentOrder.value,
        order_status: 4,
        verify_time: new Date().toISOString(),
        complete_time: new Date().toISOString()
      }
    }
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '核销取餐失败')
  }
}

const handleBatchAccept = async () => {
  const rows = multipleSelection.value.filter((item) => Number(item.order_status) === 0)
  if (!rows.length) {
    ElMessage.info('请选择待确认订单后再批量接单')
    return
  }
  try {
    await Promise.all(rows.map((row) => orderApi.updateStatus(row.order_id, { order_status: 1 })))
    ElMessage.success('批量接单成功')
    clearSelection()
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '批量接单失败')
  }
}

const handleBatchComplete = async () => {
  const rows = multipleSelection.value.filter((item) => Number(item.order_status) === 1)
  if (!rows.length) {
    ElMessage.info('请选择制作中的订单后再批量完成')
    return
  }
  try {
    await Promise.all(rows.map((row) => orderApi.updateStatus(row.order_id, { order_status: 2 })))
    ElMessage.success('批量制作完成成功')
    clearSelection()
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '批量制作完成失败')
  }
}

const clearSelection = () => {
  tableRef.value?.clearSelection()
  multipleSelection.value = []
}

const handleExport = () => {
  const rows = list.value.map((item) => ({
    订单号: item.order_no || '',
    用户: getOrderUserText(item),
    档口: getOrderStallText(item),
    订单金额: currency(pickAmount(item, ['pay_amount', 'total_amount', 'order_amount'])),
    退款状态: refundStatusText(item),
    退款金额: hasRefundRequest(item) ? currency(getRefundAmount(item)) : '0.00',
    支付状态: Number(item.pay_status) === 1 ? '已支付' : '待支付',
    订单状态: statusText(item.order_status),
    创建时间: formatDateTime(item.create_time || item.order_time)
  }))

  const headers = Object.keys(rows[0] || { 订单号: '', 用户: '', 档口: '', 订单金额: '', 退款状态: '', 退款金额: '', 支付状态: '', 订单状态: '', 创建时间: '' })
  const csv = [headers.join(','), ...rows.map((row) => headers.map((key) => `"${String(row[key]).replaceAll('"', '""')}"`).join(','))].join('\n')
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `orders-${Date.now()}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
  ElMessage.success('订单已导出')
}

const printReceipt = (row) => {
  const content = [
    '校园食堂订单小票',
    `订单号：${row.order_no || '-'}`,
    `用户：${getOrderUserText(row)}`,
    `档口：${getOrderStallText(row)}`,
    `金额：¥${currency(pickAmount(row, ['pay_amount', 'total_amount', 'order_amount']))}`,
    `退款状态：${refundStatusText(row)}`,
    `状态：${statusText(row.order_status)}`,
    `时间：${formatDateTime(row.create_time || row.order_time)}`
  ].join('\n')

  const printWindow = window.open('', '_blank', 'width=420,height=640')
  if (!printWindow) return
  printWindow.document.write(`<pre style="font-family: Microsoft YaHei; padding: 24px; white-space: pre-wrap;">${content}</pre>`)
  printWindow.document.close()
  printWindow.print()
}

const goToRefund = (row) => {
  const queryParams = {
    orderNo: row.order_no || '',
    order_id: row.order_id || '',
    from: 'orders',
    ...(hasPendingRefund(row) ? { status: 'pending' } : {})
  }
  router.push({ path: '/refunds', query: queryParams })
}

watch(
  () => route.query.highlight_order_id,
  () => {
    if (route.query.highlight_order_id) {
      loadData()
    }
  }
)

onMounted(loadData)
onBeforeUnmount(() => clearHighlightState())
</script>

<style scoped lang="scss">
.page-grid {
  display: grid;
}

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
.batch-bar,
.batch-bar__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.summary-stat,
.return-highlight-banner {
  padding: 16px 18px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
}

.summary-stat {
  span,
  p {
    color: #a9b4d0;
  }

  span {
    display: block;
    margin-bottom: 10px;
  }

  strong {
    display: block;
    margin-bottom: 8px;
    font-size: 24px;
  }

  p {
    margin: 0;
    font-size: 13px;
  }
}

.return-highlight-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
  border-color: rgba(247, 191, 90, 0.22);
  background: rgba(247, 191, 90, 0.1);

  p {
    margin: 6px 0 0;
    color: #f3d795;
  }
}

.summary-stat--accent {
  border-color: rgba(36, 201, 154, 0.2);
  background: rgba(36, 201, 154, 0.08);
}

.batch-bar {
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding: 12px 14px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
}

.batch-bar__info {
  color: #cdd5ea;
}

.order-no-cell,
.refund-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.refund-cell__amount {
  color: #f3d795;
  font-size: 13px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 22px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.detail-item,
.refund-highlight-card {
  padding: 16px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
}

.detail-item {
  span {
    display: block;
    margin-bottom: 8px;
    color: #8d98b5;
    font-size: 13px;
  }
}

.refund-highlight-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 18px;

  p {
    margin: 8px 0 0;
    color: #90a0c0;
  }
}

:deep(.order-row-highlight td) {
  background: rgba(247, 191, 90, 0.08) !important;
}
</style>

