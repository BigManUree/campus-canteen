<template>
  <div class="page-shell export-page">
    <div class="export-overview">
      <div class="export-hero">
        <p class="export-hero__eyebrow">数据导出中心</p>
        <h3>一站式导出订单与销售报表</h3>
        <span>仅保留接口文档已确认的订单导出与销售导出能力，方便先筛选再下载。</span>
      </div>

      <div class="export-metrics">
        <div class="export-metric-card">
          <span>可导出项目</span>
          <strong>{{ exportCards.length }}</strong>
        </div>
        <div class="export-metric-card">
          <span>最近导出时间</span>
          <strong>{{ lastExportTime }}</strong>
        </div>
        <div class="export-metric-card">
          <span>最近导出类型</span>
          <strong>{{ lastExportType }}</strong>
        </div>
      </div>
    </div>

    <el-alert
      class="export-boundary-alert"
      type="info"
      :closable="false"
      title="导出能力边界"
      description="当前 API 模块只接入了订单报表与销售报表两个导出接口，页面不再展示未接通的导出能力。"
    />

    <div class="export-grid">
      <el-card v-for="card in exportCards" :key="card.type" class="panel-card export-card" shadow="never">
        <template #header>
          <div class="export-card__header">
            <div>
              <h4>{{ card.title }}</h4>
              <p>{{ card.description }}</p>
            </div>
            <div class="export-card__icon">{{ card.icon }}</div>
          </div>
        </template>

        <div class="export-card__body">
          <el-form :ref="(el) => setRangeFormRef(card.type, el)" :model="ranges" :rules="rangeRules">
            <el-form-item :prop="card.type">
              <el-date-picker
                v-model="ranges[card.type]"
                type="daterange"
                value-format="YYYY-MM-DD"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
              />
            </el-form-item>
          </el-form>

          <template v-if="card.type === 'order'">
            <div class="export-filter-grid">
              <el-select v-model="filters.order.order_status" clearable placeholder="订单状态">
                <el-option v-for="item in orderStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
              <el-select v-model="filters.order.pay_status" clearable placeholder="支付状态">
                <el-option v-for="item in payStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
              <el-select
                v-model="filters.order.canteen_id"
                clearable
                filterable
                :loading="loadingCanteens"
                :disabled="isMerchantRole"
                placeholder="档口"
              >
                <el-option v-for="item in canteenOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
          </template>

          <template v-else>
            <div class="export-filter-grid export-filter-grid--sales">
              <el-select v-model="filters.sales.group_by" placeholder="分组方式">
                <el-option v-for="item in groupByOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
              <el-select
                v-model="filters.sales.canteen_id"
                clearable
                filterable
                :loading="loadingCanteens"
                :disabled="isMerchantRole"
                placeholder="档口"
              >
                <el-option v-for="item in canteenOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
          </template>

          <el-radio-group v-model="formats[card.type]" class="format-switch">
            <el-radio-button label="csv" value="csv">CSV</el-radio-button>
            <el-radio-button label="excel" value="excel">Excel</el-radio-button>
          </el-radio-group>

          <div class="export-card__tips">
            <span>{{ card.tip }}</span>
            <strong>{{ rangeSummary(card.type) }}</strong>
          </div>

          <div class="export-card__subtips">
            <span v-if="card.type === 'order'">{{ orderFilterSummary }}</span>
            <span v-else>{{ salesFilterSummary }}</span>
            <em v-if="isMerchantRole">当前为档口角色，仅显示所属档口数据</em>
          </div>

          <el-button :type="card.buttonType" :loading="exporting[card.type]" @click="handleExport(card.type)">
            {{ card.buttonText }}
          </el-button>
        </div>
      </el-card>
    </div>

    <el-card class="panel-card export-history-card" shadow="never">
      <template #header>
        <div class="section-header">
          <div>
            <h4>最近导出记录</h4>
            <p>便于回顾最近已下载的报表文件。</p>
          </div>
          <div class="section-header__actions">
            <el-button text @click="resetRanges">重置条件</el-button>
            <el-button text @click="clearHistory" :disabled="!historyList.length">清空记录</el-button>
          </div>
        </div>
      </template>

      <div v-if="historyList.length" class="history-list">
        <div v-for="item in historyList" :key="item.id" class="history-item">
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.rangeText }}</p>
        </div>
          <span>{{ item.time }}</span>
        </div>
      </div>
      <el-empty v-else description="还没有导出记录" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { exportApi } from '@/api/modules/export'
import { canteenApi } from '@/api/modules/canteens'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/formatters'

const authStore = useAuthStore()
const isMerchantRole = computed(() => ['merchant', 'canteen_admin'].includes(authStore.user?.role))

const ranges = reactive({
  order: [],
  sales: []
})
const formats = reactive({
  order: 'csv',
  sales: 'csv'
})
const exporting = reactive({ order: false, sales: false })
const historyList = ref([])
const rangeFormRefs = reactive({})
const canteenOptions = ref([])
const loadingCanteens = ref(false)
const filters = reactive({
  order: {
    order_status: undefined,
    pay_status: undefined,
    canteen_id: undefined
  },
  sales: {
    canteen_id: undefined,
    group_by: 'dish'
  }
})

const orderStatusOptions = [
  { label: '待确认', value: 0 },
  { label: '制作中', value: 1 },
  { label: '待取餐', value: 2 },
  { label: '配送中', value: 3 },
  { label: '已完成', value: 4 }
]

const payStatusOptions = [
  { label: '未支付', value: 0 },
  { label: '已支付', value: 1 }
]

const groupByOptions = [
  { label: '按菜品', value: 'dish' },
  { label: '按档口', value: 'canteen' },
  { label: '按日期', value: 'date' }
]

const validateRange = (_rule, value, callback) => {
  if (!Array.isArray(value) || value.length !== 2 || !value[0] || !value[1]) {
    callback(new Error('请选择完整的日期区间'))
    return
  }
  if (new Date(value[0]).getTime() > new Date(value[1]).getTime()) {
    callback(new Error('开始日期不能晚于结束日期'))
    return
  }
  callback()
}

const rangeRules = {
  order: [{ validator: validateRange, trigger: 'change' }],
  sales: [{ validator: validateRange, trigger: 'change' }]
}

const setRangeFormRef = (type, el) => {
  if (el) {
    rangeFormRefs[type] = el
  }
}

const exportCards = [
  {
    type: 'order',
    title: '订单报表',
    description: '支持按订单状态、支付状态、档口与时间区间导出订单报表。',
    tip: '对应后端接口：/api/statistics/export/orders',
    icon: '📦',
    buttonType: 'primary',
    buttonText: '导出订单报表'
  },
  {
    type: 'sales',
    title: '销售报表',
    description: '支持按档口、分组方式与时间区间导出销售报表。',
    tip: '对应后端接口：/api/statistics/export/sales',
    icon: '📈',
    buttonType: 'success',
    buttonText: '导出销售报表'
  }
]

const getContentDispositionFileName = (headers) => {
  const disposition = headers?.['content-disposition'] || headers?.['Content-Disposition']
  if (!disposition) return ''

  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]).replace(/"/g, '')
    } catch {
      return utf8Match[1].replace(/"/g, '')
    }
  }

  const normalMatch = disposition.match(/filename=([^;]+)/i)
  if (!normalMatch?.[1]) return ''
  return normalMatch[1].trim().replace(/^"|"$/g, '')
}

const saveBlob = (blob, fileName) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  link.click()
  window.URL.revokeObjectURL(url)
}

const rangeSummary = (type) => {
  const currentRange = ranges[type]
  if (!currentRange?.length) return '默认导出全部时间范围'
  return `${currentRange[0]} 至 ${currentRange[1]}`
}

const orderFilterSummary = computed(() => {
  const parts = []
  const orderStatus = orderStatusOptions.find((item) => item.value === filters.order.order_status)?.label
  const payStatus = payStatusOptions.find((item) => item.value === filters.order.pay_status)?.label
  const canteenName = canteenOptions.value.find((item) => Number(item.value) === Number(filters.order.canteen_id))?.label

  if (orderStatus) parts.push(orderStatus)
  if (payStatus) parts.push(payStatus)
  if (canteenName) parts.push(canteenName)

  return parts.length ? parts.join(' / ') : '未附加更多筛选条件'
})

const salesFilterSummary = computed(() => {
  const parts = []
  const groupBy = groupByOptions.find((item) => item.value === filters.sales.group_by)?.label
  const canteenName = canteenOptions.value.find((item) => Number(item.value) === Number(filters.sales.canteen_id))?.label

  if (groupBy) parts.push(groupBy)
  if (canteenName) parts.push(canteenName)

  return parts.join(' / ')
})

const recordHistory = (type, fileName) => {
  const title = type === 'order' ? '订单报表' : '销售报表'
  const filterText = type === 'order' ? orderFilterSummary.value : salesFilterSummary.value
  historyList.value.unshift({
    id: `${type}-${Date.now()}`,
    title: `${title} · ${fileName}`,
    rangeText: `${rangeSummary(type)} · ${filterText} · ${formats[type].toUpperCase()}`,
    time: formatDateTime(new Date())
  })
  historyList.value = historyList.value.slice(0, 6)
}

const buildFileName = (type, format) => {
  const suffix = format === 'excel' ? 'xlsx' : 'csv'
  const stamp = formatDateTime(new Date()).replace(/[-: ]/g, '').slice(0, 14)
  return `${type === 'order' ? 'orders' : 'sales'}_${stamp}.${suffix}`
}

const getOrderParams = () => ({
  start_date: ranges.order?.[0],
  end_date: ranges.order?.[1],
  order_status: filters.order.order_status,
  pay_status: filters.order.pay_status,
  canteen_id: filters.order.canteen_id,
  format: formats.order
})

const getSalesParams = () => ({
  start_date: ranges.sales?.[0],
  end_date: ranges.sales?.[1],
  canteen_id: filters.sales.canteen_id,
  group_by: filters.sales.group_by,
  format: formats.sales
})

const loadCanteens = async () => {
  loadingCanteens.value = true
  try {
    const result = await canteenApi.getList({ page: 1, page_size: 100 })
    const source = Array.isArray(result)
      ? result
      : result?.items || result?.list || result?.rows || result?.data?.items || result?.data || []
    canteenOptions.value = source.map((item) => ({
      label: item.canteen_name || item.name || `档口 ${item.canteen_id}`,
      value: Number(item.canteen_id || item.id)
    })).filter((item) => Number.isFinite(item.value))

    const currentUserCanteenId = Number(
      authStore.user?.canteen_id ||
      authStore.user?.merchant?.canteen_id ||
      authStore.user?.canteen?.canteen_id ||
      authStore.user?.canteen?.id
    )

    if (isMerchantRole.value && Number.isFinite(currentUserCanteenId)) {
      filters.order.canteen_id = currentUserCanteenId
      filters.sales.canteen_id = currentUserCanteenId
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载档口筛选项失败')
  } finally {
    loadingCanteens.value = false
  }
}

const handleExport = async (type) => {
  try {
    await rangeFormRefs[type]?.validate()
  } catch {
    ElMessage.warning('请先选择完整的日期区间后再导出')
    return
  }
  const format = formats[type]
  const fallbackFileName = buildFileName(type, format)

  exporting[type] = true
  try {
    const response = type === 'order'
      ? await exportApi.exportOrders(getOrderParams())
      : await exportApi.exportSales(getSalesParams())
    const blob = response?.data || response
    const fileName = getContentDispositionFileName(response?.headers) || fallbackFileName
    saveBlob(blob, fileName)
    recordHistory(type, fileName)
    ElMessage.success('报表导出成功')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '报表导出失败')
  } finally {
    exporting[type] = false
  }
}

const resetRanges = () => {
  ranges.order = []
  ranges.sales = []
  formats.order = 'csv'
  formats.sales = 'csv'
  filters.order.order_status = undefined
  filters.order.pay_status = undefined
  filters.sales.group_by = 'dish'
  if (!isMerchantRole.value) {
    filters.order.canteen_id = undefined
    filters.sales.canteen_id = undefined
  }
  Object.values(rangeFormRefs).forEach((formRef) => {
    formRef?.resetFields()
    formRef?.clearValidate()
  })
  ElMessage.success('导出条件已重置')
}

const clearHistory = () => {
  historyList.value = []
  ElMessage.success('导出记录已清空')
}

const lastExportRecord = computed(() => historyList.value[0] || null)
const lastExportTime = computed(() => lastExportRecord.value?.time || '暂无记录')
const lastExportType = computed(() => lastExportRecord.value?.title?.split(' · ')[0] || '暂无记录')

onMounted(() => {
  loadCanteens()
})
</script>

<style scoped lang="scss">
.export-page,
.export-grid,
.history-list {
  display: grid;
  gap: 20px;
}

.export-overview {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 1fr);
  gap: 20px;
}

.export-hero,
.export-metric-card,
.export-card,
.history-item {
  border: 1px solid rgba(151, 164, 199, 0.14);
  background: rgba(255, 255, 255, 0.03);
}

.export-boundary-alert {
  margin-top: -4px;
}

.export-hero {
  padding: 28px;
  border-radius: 26px;

  &__eyebrow {
    margin: 0 0 10px;
    font-size: 13px;
    letter-spacing: 0.2em;
    color: #63e6be;
    text-transform: uppercase;
  }

  h3 {
  margin: 0;
    font-size: 30px;
}

  span {
    display: block;
    margin-top: 12px;
    color: #90a0c0;
    line-height: 1.8;
  }
}

.export-metrics {
  display: grid;
  gap: 16px;
}

.export-metric-card,
.history-item {
  padding: 18px 20px;
  border-radius: 22px;
}

.export-metric-card {
  span {
    color: #90a0c0;
  }

  strong {
    display: block;
    margin-top: 10px;
    font-size: 24px;
  }
}

.export-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.export-card {
  border-radius: 24px;
}

.export-card__header,
.history-item,
.section-header,
.section-header__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.export-card__header {
  h4 {
    margin: 0;
    font-size: 20px;
  }

  p {
    margin: 8px 0 0;
    color: #8d98b5;
  }
}

.export-card__icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.06);
  font-size: 26px;
}

.export-card__body,
.export-filter-grid {
  display: grid;
  gap: 16px;
}

.format-switch,
.export-card__tips,
.export-card__subtips {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px;
}

.export-card__tips span,
.export-card__subtips span {
  color: #90a0c0;
}

.export-card__subtips em {
  color: #63e6be;
  font-style: normal;
}

.history-item {
  align-items: flex-start;

  p,
  span {
    color: #90a0c0;
  }

  p {
    margin: 8px 0 0;
  }
}
</style>
