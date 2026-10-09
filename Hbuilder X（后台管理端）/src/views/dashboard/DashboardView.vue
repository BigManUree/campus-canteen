<template>
  <div class="page-shell dashboard-page">
    <section class="hero-strip">
      <div>
        <p class="hero-strip__eyebrow">运营总览</p>
        <h3>欢迎回来，{{ authStore.userName }}</h3>
        <span>快速掌握今日订单、销售额与待处理任务，进入核心模块继续处理。</span>
      </div>
      <div class="hero-strip__actions">
        <el-button type="primary" size="large" @click="loadData" :loading="loading">刷新看板</el-button>
      </div>
    </section>

    <div class="quick-links">
      <button v-for="item in quickLinks" :key="item.path" type="button" class="quick-link" @click="router.push(item.path)">
        <strong>{{ item.title }}</strong>
        <span>{{ item.description }}</span>
      </button>
    </div>

    <div class="metric-grid">
      <el-card v-for="item in metrics" :key="item.label" class="panel-card metric-card" shadow="never">
        <div class="metric-card__icon" :style="{ background: item.gradient }">{{ item.icon }}</div>
        <div>
          <p>{{ item.label }}</p>
          <h4>{{ item.value }}</h4>
          <span>{{ item.tip }}</span>
        </div>
      </el-card>
    </div>

    <div class="pulse-grid">
      <el-card class="panel-card pulse-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <h4>经营脉搏</h4>
              <p>用关键指标的相对高度快速判断今天的经营节奏。</p>
            </div>
          </div>
        </template>
        <div class="pulse-list">
          <div v-for="item in pulseCards" :key="item.label" class="pulse-item">
            <div class="pulse-item__meta">
              <strong>{{ item.label }}</strong>
              <span>{{ item.valueText }}</span>
            </div>
            <div class="pulse-item__track">
              <div class="pulse-item__fill" :style="{ width: `${item.percent}%`, background: item.gradient }"></div>
            </div>
            <p>{{ item.tip }}</p>
          </div>
        </div>
      </el-card>

      <el-card class="panel-card pulse-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <h4>今日速览</h4>
              <p>将今日订单、销售额和待处理项拆成更直观的业务摘要。</p>
            </div>
          </div>
        </template>
        <div class="snapshot-grid">
          <div v-for="item in snapshotCards" :key="item.label" class="snapshot-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.tip }}</p>
          </div>
        </div>
      </el-card>
    </div>

    <div class="quick-grid">
      <el-card class="panel-card quick-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <h4>经营提醒</h4>
              <p>按概览统计结果聚合关键提醒</p>
            </div>
          </div>
        </template>
        <div class="alert-list">
          <div v-for="item in alertCards" :key="item.title" class="alert-item">
            <div class="alert-item__icon" :style="{ background: item.gradient }">{{ item.icon }}</div>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.description }}</p>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="panel-card quick-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div>
              <h4>概览数据状态</h4>
              <p>根据真实接口字段展示看板当前拿到的数据项。</p>
            </div>
          </div>
        </template>
        <div class="overview-keys overview-keys--simple">
          <div v-for="item in overviewKeys" :key="item.label" class="overview-key-card">
            <strong>{{ item.label }}</strong>
            <span>{{ item.value }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { dashboardApi } from '@/api/modules/dashboard'
import { useAuthStore } from '@/stores/auth'
import { currency } from '@/utils/formatters'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const overview = ref({})

const quickLinks = [
  { path: '/orders', title: '订单管理', description: '快速进入履约与处理中心' },
  { path: '/refunds', title: '退款管理', description: '优先处理售后与审批工单' },
  { path: '/notifications', title: '通知中心', description: '查看系统消息与未读通知' },
  { path: '/statistics', title: '统计分析', description: '查看销量、热度与偏好统计' }
]

const getTodayOrders = () => Number(overview.value?.todayOrderCount ?? 0)
const getTodaySales = () => Number(overview.value?.todaySalesAmount ?? 0)
const getPendingOrders = () => Number(overview.value?.pendingOrderCount ?? 0)
const getTodayUsers = () => Number(overview.value?.todayNewUserCount ?? 0)
const getPendingRefunds = () => Number(overview.value?.pendingRefundCount ?? 0)
const getActiveStalls = () => Number(overview.value?.activeStallCount ?? 0)

const metrics = computed(() => [
  {
    label: '今日订单',
    value: getTodayOrders(),
    tip: '来自 dashboard.todayOrderCount',
    icon: '📦',
    gradient: 'linear-gradient(135deg, #24c99a, #6ea8fe)'
  },
  {
    label: '今日销售额',
    value: `¥${currency(getTodaySales())}`,
    tip: '来自 dashboard.todaySalesAmount',
    icon: '💰',
    gradient: 'linear-gradient(135deg, #ffb84d, #ff7a59)'
  },
  {
    label: '待处理订单',
    value: getPendingOrders(),
    tip: '来自 dashboard.pendingOrderCount',
    icon: '⏳',
    gradient: 'linear-gradient(135deg, #ff6b81, #ff9f6e)'
  },
  {
    label: '今日新增用户',
    value: getTodayUsers(),
    tip: '来自 dashboard.todayNewUserCount',
    icon: '👥',
    gradient: 'linear-gradient(135deg, #6ea8fe, #9b7bff)'
  }
])

const pulseCards = computed(() => {
  const todayOrders = getTodayOrders()
  const todaySales = getTodaySales()
  const pendingOrders = getPendingOrders()
  const values = [todayOrders, todaySales, pendingOrders]
  const maxValue = Math.max(...values, 1)

  return [
    {
      label: '订单节奏',
      valueText: `${todayOrders} 单`,
      percent: Math.max(10, Math.round((todayOrders / maxValue) * 100)),
      gradient: 'linear-gradient(90deg, #24c99a, #6ea8fe)',
      tip: '订单量越高，说明当前经营节奏越活跃。'
    },
    {
      label: '销售动能',
      valueText: `¥${currency(todaySales)}`,
      percent: Math.max(10, Math.round((todaySales / maxValue) * 100)),
      gradient: 'linear-gradient(90deg, #ffb84d, #ff7a59)',
      tip: '结合订单量判断客单价与销售效率。'
    },
    {
      label: '履约压力',
      valueText: `${pendingOrders} 单`,
      percent: Math.max(10, Math.round((pendingOrders / maxValue) * 100)),
      gradient: 'linear-gradient(90deg, #ff6b81, #ff9f6e)',
      tip: '待处理订单偏高时，建议优先分配人手。'
    }
  ]
})

const snapshotCards = computed(() => {
  const todayOrders = getTodayOrders()
  const todaySales = getTodaySales()
  const pendingOrders = getPendingOrders()
  const todayUsers = getTodayUsers()
  return [
    {
      label: '平均订单价值',
      value: todayOrders ? `¥${currency(todaySales / todayOrders)}` : '¥0.00',
      tip: '按今日销售额 / 今日订单数估算'
    },
    {
      label: '待处理占比',
      value: todayOrders ? `${Math.round((pendingOrders / Math.max(todayOrders, 1)) * 100)}%` : '0%',
      tip: '用于判断当前履约压力'
    },
    {
      label: '新增用户节奏',
      value: `${todayUsers}`,
      tip: '今日新增用户数，可用于观察拉新表现'
    },
    {
      label: '活跃档口数',
      value: `${getActiveStalls()}`,
      tip: '当前有经营动作的档口数量'
    }
  ]
})

const alertCards = computed(() => [
  {
    title: '待处理订单提醒',
    description: `当前待处理订单 ${getPendingOrders()} 笔，建议优先跟进。`,
    icon: '↺',
    gradient: 'linear-gradient(135deg, rgba(255, 107, 129, 0.22), rgba(255, 159, 110, 0.22))'
  },
  {
    title: '退款审批提醒',
    description: `当前待审核退款 ${getPendingRefunds()} 笔，可前往退款页集中处理。`,
    icon: '¤',
    gradient: 'linear-gradient(135deg, rgba(255, 184, 77, 0.18), rgba(255, 122, 89, 0.2))'
  },
  {
    title: '新增用户观察',
    description: `今日新增用户 ${getTodayUsers()} 人，可结合转化表现继续复盘。`,
    icon: '◎',
    gradient: 'linear-gradient(135deg, rgba(110, 168, 254, 0.2), rgba(155, 123, 255, 0.18))'
  }
])

const overviewKeys = computed(() => {
  const data = overview.value || {}
  return [
    { label: 'todayOrderCount', value: data.todayOrderCount ?? '未返回' },
    { label: 'todaySalesAmount', value: data.todaySalesAmount ?? '未返回' },
    { label: 'todayNewUserCount', value: data.todayNewUserCount ?? '未返回' },
    { label: 'pendingOrderCount', value: data.pendingOrderCount ?? '未返回' },
    { label: 'pendingRefundCount', value: data.pendingRefundCount ?? '未返回' },
    { label: 'activeStallCount', value: data.activeStallCount ?? '未返回' }
  ]
})

const loadData = async () => {
  loading.value = true
  try {
    const overviewResult = await dashboardApi.getOverview()
    overview.value = overviewResult?.data || overviewResult || {}
    ElMessage.success('看板数据已刷新')
  } catch (error) {
    ElMessage.error(error?.userMessage || error?.message || '刷新看板失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.dashboard-page {
  display: grid;
  gap: 20px;
}

.hero-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 24px 28px;
  border: 1px solid rgba(151, 164, 199, 0.12);
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(36, 201, 154, 0.14), rgba(110, 168, 254, 0.12));

  h3 {
    margin: 6px 0 10px;
    font-size: 30px;
  }

  span {
    color: #a5b0cc;
  }
}

.hero-strip__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hero-strip__eyebrow {
  margin: 0;
  color: #63e6be;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
}

.quick-links,
.metric-grid,
.quick-grid,
.overview-keys,
.pulse-grid,
.snapshot-grid {
  display: grid;
  gap: 20px;
}

.quick-links {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.quick-link {
  padding: 18px 20px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  color: #f3f7ff;
  text-align: left;
  cursor: pointer;

  strong {
    display: block;
    margin-bottom: 8px;
    font-size: 18px;
  }

  span {
    color: #9aa8c7;
    line-height: 1.7;
  }
}

.quick-link:hover {
  border-color: rgba(36, 201, 154, 0.22);
  background: rgba(36, 201, 154, 0.08);
}

.metric-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.pulse-grid,
.quick-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.quick-card,
.pulse-card {
  min-height: 100%;
}

.metric-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 18px;
}

.metric-card__icon,
.alert-item__icon {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  border-radius: 20px;
  font-size: 30px;
}

.metric-card p,
.section-header p,
.alert-item p,
.overview-key-card span,
.pulse-item p,
.snapshot-card p {
  color: #90a0c0;
}

.metric-card p {
  margin: 0 0 10px;
}

.metric-card h4 {
  margin: 0 0 8px;
  font-size: 28px;
}

.pulse-list {
  display: grid;
  gap: 18px;
}

.pulse-item,
.alert-item,
.overview-key-card,
.snapshot-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.03);
}

.pulse-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.pulse-item__track {
  height: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.pulse-item__fill {
  height: 100%;
  border-radius: inherit;
}

.pulse-item p,
.alert-item p,
.snapshot-card p {
  margin: 12px 0 0;
  line-height: 1.7;
}

.snapshot-grid,
.overview-keys--simple {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.snapshot-card strong,
.overview-key-card strong {
  display: block;
  margin-top: 12px;
  font-size: 22px;
}

.alert-list {
  display: grid;
  gap: 14px;
}

.alert-item {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;

  h4 {
    margin: 0;
    font-size: 20px;
  }

  p {
    margin: 8px 0 0;
  }
}
</style>
