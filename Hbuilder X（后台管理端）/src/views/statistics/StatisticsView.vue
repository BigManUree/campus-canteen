<template>
  <div class="page-shell stats-page">
    <el-card class="panel-card stats-toolbar-card" shadow="never">
      <div class="stats-toolbar">
        <div>
          <p class="stats-toolbar__eyebrow">经营洞察台</p>
          <h3>统计分析</h3>
          <p>基于新的后台统计接口展示销售趋势、菜品排行、档口排行、用户增长与退款汇总。</p>
        </div>
        <div class="stats-toolbar__actions">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 260px"
          />
          <el-select
            v-model="filters.canteen_id"
            clearable
            filterable
            :loading="loadingCanteens"
            :disabled="isMerchantRole"
            placeholder="档口"
            style="width: 180px"
          >
            <el-option v-for="item in canteenOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="filters.groupBy" placeholder="趋势粒度" style="width: 140px">
            <el-option v-for="item in groupByOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-button type="primary" :loading="loading" @click="loadData">刷新</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div class="stats-toolbar__subtips">
        <span>当前时间：{{ rangeLabel }}</span>
        <span>档口范围：{{ canteenLabel }}</span>
        <span>趋势粒度：{{ groupByLabel }}</span>
        <em v-if="isMerchantRole">当前为档口角色，后端会自动限制为所属档口数据</em>
      </div>

      <div class="stats-hero-grid">
        <div class="stats-hero-card stats-hero-card--accent">
          <span>统计口径</span>
          <strong>{{ rangeLabel }}</strong>
          <p>所有指标都基于当前时间范围与档口筛选重新计算。</p>
        </div>
        <div v-for="item in overviewCards" :key="item.label" class="stats-hero-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.tip }}</p>
        </div>
      </div>
    </el-card>

    <div class="stats-grid">
      <el-card class="panel-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <h3>销售趋势</h3>
              <p>基于后台销售趋势接口展示订单数和销售额变化</p>
            </div>
            <span class="section-header__meta">共 {{ salesTrend.length }} 个节点</span>
          </div>
        </template>
        <div class="trend-list" v-loading="loading">
          <div v-for="(item, index) in salesTrend" :key="index" class="trend-item">
            <strong>{{ item.date || item.stat_date || item.name || `数据 ${index + 1}` }}</strong>
            <span>订单 {{ item.orderCount ?? item.order_count ?? 0 }}</span>
            <span>销售额 ¥{{ currency(item.salesAmount ?? item.totalAmount ?? item.total_amount ?? 0) }}</span>
          </div>
          <el-empty v-if="!salesTrend.length && !loading" description="暂无销售趋势数据" />
        </div>
      </el-card>

      <el-card class="panel-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <h3>退款汇总</h3>
              <p>查看退款单数、退款金额与退款率</p>
            </div>
          </div>
        </template>
        <div class="refund-summary" v-loading="loading">
          <div class="refund-summary__card">
            <span>退款单数</span>
            <strong>{{ refundSummary.refundCount ?? 0 }}</strong>
          </div>
          <div class="refund-summary__card">
            <span>退款金额</span>
            <strong>¥{{ currency(refundSummary.refundAmount ?? 0) }}</strong>
          </div>
          <div class="refund-summary__card">
            <span>退款率</span>
            <strong>{{ formatPercent(refundSummary.refundRate) }}</strong>
          </div>
        </div>
      </el-card>
    </div>

    <div class="stats-grid stats-grid--bottom">
      <el-card class="panel-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <h3>菜品排行</h3>
              <p>按销量与销售额展示当前热卖菜品</p>
            </div>
            <span class="section-header__meta">共 {{ dishRanking.length }} 项</span>
          </div>
        </template>
        <div class="stat-list" v-loading="loading">
          <div v-for="(item, index) in dishRanking" :key="index" class="stat-row">
            <div>
              <strong>{{ item.dish_name || item.name || '未命名菜品' }}</strong>
              <p>销量 {{ item.salesCount ?? item.sales_count ?? item.total_quantity ?? 0 }} 份</p>
            </div>
            <span>¥{{ currency(item.salesAmount ?? item.totalAmount ?? item.total_amount ?? 0) }}</span>
          </div>
          <el-empty v-if="!dishRanking.length && !loading" description="暂无菜品排行数据" />
        </div>
      </el-card>

      <el-card class="panel-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <h3>档口排行</h3>
              <p>按订单数与销售额展示经营表现</p>
            </div>
            <span class="section-header__meta">共 {{ stallRanking.length }} 项</span>
          </div>
        </template>
        <div class="stat-list" v-loading="loading">
          <div v-for="(item, index) in stallRanking" :key="index" class="stat-row">
            <div>
              <strong>{{ item.stall_name || item.canteen_name || item.name || `档口 ${index + 1}` }}</strong>
              <p>订单 {{ item.orderCount ?? item.order_count ?? 0 }} 单</p>
            </div>
            <span>¥{{ currency(item.salesAmount ?? item.totalAmount ?? item.total_amount ?? 0) }}</span>
          </div>
          <el-empty v-if="!stallRanking.length && !loading" description="暂无档口排行数据" />
        </div>
      </el-card>
    </div>

    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="section-header">
          <div>
            <h3>用户增长</h3>
            <p>展示当前时间范围内新增用户趋势</p>
          </div>
        </div>
      </template>
      <div class="preference-grid" v-loading="loading">
        <div v-for="(item, index) in userGrowth" :key="index" class="preference-card">
          <strong>{{ item.date || item.stat_date || `节点 ${index + 1}` }}</strong>
          <p>新增用户 {{ item.newUserCount ?? item.new_user_count ?? item.count ?? 0 }}</p>
          <span>用于观察拉新节奏变化</span>
        </div>
        <el-empty v-if="!userGrowth.length && !loading" description="暂无用户增长数据" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { statisticsApi } from '@/api/modules/statistics'
import { canteenApi } from '@/api/modules/canteens'
import { useAuthStore } from '@/stores/auth'
import { currency } from '@/utils/formatters'

const authStore = useAuthStore()
const isMerchantRole = computed(() => ['merchant', 'canteen_admin'].includes(authStore.user?.role))

const loading = ref(false)
const loadingCanteens = ref(false)
const salesTrend = ref([])
const dishRanking = ref([])
const stallRanking = ref([])
const userGrowth = ref([])
const refundSummary = ref({})
const dateRange = ref([])
const canteenOptions = ref([])

const filters = reactive({
  canteen_id: undefined,
  groupBy: 'day'
})

const groupByOptions = [
  { label: '按日', value: 'day' },
  { label: '按周', value: 'week' },
  { label: '按月', value: 'month' }
]

const rangeLabel = computed(() => {
  if (!dateRange.value?.length) return '全部时间范围'
  return `${dateRange.value[0]} 至 ${dateRange.value[1]}`
})

const canteenLabel = computed(() => {
  const selected = canteenOptions.value.find((item) => Number(item.value) === Number(filters.canteen_id))
  return selected?.label || '全部档口'
})

const groupByLabel = computed(() => groupByOptions.find((item) => item.value === filters.groupBy)?.label || '按日')

const overviewCards = computed(() => {
  const totalSales = salesTrend.value.reduce((sum, item) => sum + Number(item.salesAmount ?? item.totalAmount ?? item.total_amount ?? 0), 0)
  const totalOrders = salesTrend.value.reduce((sum, item) => sum + Number(item.orderCount ?? item.order_count ?? 0), 0)
  const totalUsers = userGrowth.value.reduce((sum, item) => sum + Number(item.newUserCount ?? item.new_user_count ?? item.count ?? 0), 0)
  const topDish = dishRanking.value[0]

  return [
    { label: '总销售额', value: `¥${currency(totalSales)}`, tip: '汇总销售趋势接口结果' },
    { label: '总订单数', value: totalOrders, tip: '汇总销售趋势接口中的订单数字段' },
    { label: '新增用户', value: totalUsers, tip: '汇总用户增长接口结果' },
    { label: '热卖菜品', value: topDish?.dish_name || topDish?.name || '暂无数据', tip: topDish ? `销量 ${topDish.salesCount ?? topDish.sales_count ?? topDish.total_quantity ?? 0} 份` : '等待排行接口返回' }
  ]
})

const normalizeArrayPayload = (payload) => {
  const source = payload?.data && !Array.isArray(payload.data) ? payload.data : payload
  if (Array.isArray(source)) return source
  if (Array.isArray(source?.records)) return source.records
  if (Array.isArray(source?.items)) return source.items
  if (Array.isArray(source?.list)) return source.list
  if (Array.isArray(source?.rows)) return source.rows
  if (Array.isArray(source?.data)) return source.data
  return []
}

const normalizeObjectPayload = (payload) => payload?.data || payload || {}

const getBaseParams = () => ({
  startTime: dateRange.value?.[0],
  endTime: dateRange.value?.[1],
  groupBy: filters.groupBy
})

const formatPercent = (value) => {
  const amount = Number(value ?? 0)
  if (!Number.isFinite(amount)) return '0%'
  return amount <= 1 ? `${(amount * 100).toFixed(2)}%` : `${amount.toFixed(2)}%`
}

const loadCanteens = async () => {
  loadingCanteens.value = true
  try {
    const result = await canteenApi.getList({ page: 1, page_size: 100 })
    const normalized = Array.isArray(result)
      ? { items: result }
      : (result?.items ? { items: result.items } : (result?.data?.items ? { items: result.data.items } : result))
    const items = normalized?.items || normalized?.list || normalized?.rows || normalized?.data || []
    canteenOptions.value = items.map((item) => ({
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
      filters.canteen_id = currentUserCanteenId
    }
  } catch (error) {
    ElMessage.error(error?.userMessage || error?.message || '加载档口列表失败')
  } finally {
    loadingCanteens.value = false
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = getBaseParams()
    const [trendResult, dishResult, stallResult, growthResult, refundResult] = await Promise.all([
      statisticsApi.getSalesTrend(params),
      statisticsApi.getDishRanking(params),
      statisticsApi.getStallRanking(params),
      isMerchantRole.value ? Promise.resolve([]) : statisticsApi.getUserGrowth(params),
      statisticsApi.getRefundSummary(params)
    ])

    salesTrend.value = normalizeArrayPayload(trendResult)
    dishRanking.value = normalizeArrayPayload(dishResult)
    stallRanking.value = normalizeArrayPayload(stallResult)
    userGrowth.value = normalizeArrayPayload(growthResult)
    refundSummary.value = normalizeObjectPayload(refundResult)
    ElMessage.success('统计数据已刷新')
  } catch (error) {
    ElMessage.error(error?.userMessage || error?.message || '刷新统计数据失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  dateRange.value = []
  filters.groupBy = 'day'
  filters.canteen_id = isMerchantRole.value ? filters.canteen_id : undefined
  ElMessage.success('统计筛选条件已重置')
  loadData()
}

onMounted(async () => {
  await loadCanteens()
  await loadData()
})
</script>

<style scoped lang="scss">
.stats-page,
.stats-grid,
.stat-list,
.preference-grid,
.trend-list,
.refund-summary {
  display: grid;
  gap: 20px;
}

.stats-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.stats-grid--bottom {
  align-items: start;
}

.stats-toolbar-card {
  overflow: hidden;
}

.stats-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;

  h3 {
    margin: 0;
    font-size: 22px;
  }

  p {
    margin: 8px 0 0;
    color: #8d98b5;
  }
}

.stats-toolbar__eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #63e6be;
}

.stats-toolbar__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
}

.stats-toolbar__subtips {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);

  span {
    color: #c9d4ee;
  }

  em {
    color: #63e6be;
    font-style: normal;
  }
}

.stats-hero-grid {
  display: grid;
  grid-template-columns: 1.2fr repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.stats-hero-card,
.stat-row,
.preference-card,
.trend-item,
.refund-summary__card {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(151, 164, 199, 0.12);
  background: rgba(255, 255, 255, 0.03);
}

.stats-hero-card {
  span,
  p {
    color: #90a0c0;
  }

  strong {
    display: block;
    margin: 10px 0 8px;
    font-size: 22px;
  }
}

.stats-hero-card--accent {
  background: linear-gradient(135deg, rgba(36, 201, 154, 0.12), rgba(110, 168, 254, 0.12));

  strong {
    font-size: 26px;
  }
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;

  h3 {
    margin: 0;
    font-size: 20px;
  }

  p {
    margin: 8px 0 0;
    color: #8d98b5;
  }
}

.section-header__meta {
  color: #90a0c0;
}

.stat-row,
.trend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;

  p {
    margin: 8px 0 0;
    color: #90a0c0;
  }
}

.preference-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.preference-card {
  p {
    margin: 10px 0 8px;
    color: #90a0c0;
  }

  span {
    color: #63e6be;
  }
}

.refund-summary {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.refund-summary__card {
  span {
    display: block;
    margin-bottom: 10px;
    color: #90a0c0;
  }

  strong {
    font-size: 24px;
  }
}
</style>
