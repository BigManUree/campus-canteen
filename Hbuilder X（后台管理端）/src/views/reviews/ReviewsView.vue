<template>
  <div class="page-shell review-page">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>评价查看</h3>
            <p>当前接口仅支持查询评价列表，因此此页定位为评价查看与口碑巡检，不提供后台删除。</p>
          </div>
          <div class="toolbar-actions">
            <el-input v-model="query.dish_id" clearable placeholder="菜品 ID" style="width: 140px" @clear="handleFilterChange" @keyup.enter="handleSearch" />
            <el-input v-model="query.canteen_id" clearable placeholder="档口 ID" style="width: 140px" @clear="handleFilterChange" @keyup.enter="handleSearch" />
            <el-select v-model="query.rating" clearable placeholder="评分" style="width: 140px" @change="handleFilterChange">
              <el-option v-for="item in [1,2,3,4,5]" :key="item" :label="`${item} 星`" :value="item" />
            </el-select>
            <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </div>
      </template>

      <div class="review-summary">
        <div class="review-summary__hero">
          <span>评价巡检</span>
          <strong>{{ pagination.total }}</strong>
          <p>当前筛选条件下的评价数量</p>
        </div>
        <div class="review-summary__stats">
          <div v-for="item in scoreCards" :key="item.label" class="review-summary__card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.tip }}</p>
          </div>
        </div>
      </div>

      <div class="review-note">
        <el-alert
          title="能力边界说明"
          type="info"
          :closable="false"
          description="接口文档当前仅确认了评价列表查询能力，未确认管理端删除接口可安全使用，因此页面保留详情查看，不再提供删除操作。"
        />
      </div>

      <el-table :data="list" v-loading="loading" row-key="review_id">
        <el-table-column prop="review_id" label="评价 ID" min-width="100" />
        <el-table-column label="评分" min-width="160">
          <template #default="{ row }">
            <div class="rating-cell">
            <el-rate :model-value="Number(row.rating || 0)" disabled />
              <span>{{ Number(row.rating || 0).toFixed(1) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="评价用户" min-width="150">
          <template #default="{ row }">{{ row.username || row.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column label="菜品 / 订单" min-width="220">
          <template #default="{ row }">{{ row.dish_name || '-' }} / {{ row.order_no || '-' }}</template>
        </el-table-column>
        <el-table-column prop="content" label="评价内容" min-width="320" show-overflow-tooltip />
        <el-table-column label="创建时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="120">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          background
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" size="520px" title="评价详情">
      <template v-if="currentReview">
        <div class="review-detail-stack">
          <div class="review-detail-card">
            <span>评价用户</span>
            <strong>{{ currentReview.username || currentReview.nickname || '匿名用户' }}</strong>
          </div>
          <div class="review-detail-card">
            <span>关联菜品</span>
            <strong>{{ currentReview.dish_name || '未关联菜品' }}</strong>
          </div>
          <div class="review-detail-card">
            <span>关联订单</span>
            <strong>{{ currentReview.order_no || '-' }}</strong>
          </div>
          <div class="review-detail-card">
            <span>评分</span>
            <el-rate :model-value="Number(currentReview.rating || 0)" disabled />
          </div>
          <div class="review-detail-card review-detail-card--content">
            <span>评价内容</span>
            <p>{{ currentReview.content || '未填写评价内容' }}</p>
          </div>
          <div class="review-detail-card">
            <span>提交时间</span>
            <strong>{{ formatDateTime(currentReview.create_time) }}</strong>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { reviewApi } from '@/api/modules/reviews'
import { formatDateTime, normalizeListPayload } from '@/utils/formatters'

const loading = ref(false)
const list = ref([])
const currentReview = ref(null)
const detailVisible = ref(false)
const pagination = reactive({ total: 0 })
const query = reactive({ page: 1, page_size: 20, dish_id: '', canteen_id: '', rating: undefined })

const scoreCards = computed(() => {
  const total = list.value.length
  const scores = [5, 4, 3, 2, 1].map((score) => ({
    label: `${score} 星评价`,
    value: list.value.filter((item) => Number(item.rating) === score).length,
    tip: score >= 4 ? '高满意度内容' : score === 3 ? '中性反馈' : '需要重点关注'
  }))
  const average = total
    ? (list.value.reduce((sum, item) => sum + Number(item.rating || 0), 0) / total).toFixed(1)
    : '0.0'

  return [
    { label: '平均评分', value: average, tip: '按当前页评价实时计算' },
    ...scores.slice(0, 3)
  ]
})

const loadData = async () => {
  loading.value = true
  try {
    const result = await reviewApi.getList({
      page: query.page,
      page_size: query.page_size,
      dish_id: query.dish_id || undefined,
      rating: query.rating
    })
    const normalized = normalizeListPayload(result)
    list.value = normalized.items.filter((item) => {
      if (!query.canteen_id) return true
      return String(item.canteen_id || item.canteen?.canteen_id || '') === String(query.canteen_id)
    })
    pagination.total = query.canteen_id ? list.value.length : normalized.total
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载评价列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.page = 1
  loadData()
}

const handleFilterChange = () => {
  query.page = 1
  loadData()
}

const handlePageChange = (page) => {
  query.page = page
  loadData()
}

const handlePageSizeChange = (pageSize) => {
  query.page = 1
  query.page_size = pageSize
  loadData()
}

const resetFilters = () => {
  query.page = 1
  query.page_size = 20
  query.dish_id = ''
  query.canteen_id = ''
  query.rating = undefined
  loadData()
}

const openDetail = (row) => {
  currentReview.value = row
  detailVisible.value = true
  ElMessage.info('已打开评价详情')
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.review-page {
  display: grid;
  gap: 20px;
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
.pagination-wrap {
  display: flex;
  gap: 12px;
}

.review-summary {
  display: grid;
  grid-template-columns: minmax(240px, 1.1fr) minmax(0, 2fr);
  gap: 18px;
  margin-bottom: 18px;
}

.review-summary__hero,
.review-summary__card,
.review-detail-card {
  padding: 16px 18px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
}

.review-summary__hero {
  display: grid;
  gap: 8px;

  span,
  p {
    color: #8d98b5;
  }

  strong {
    font-size: 34px;
  }
}

.review-summary__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.review-summary__card {
  span,
  p {
    color: #8d98b5;
  }

  strong {
    display: block;
    margin: 10px 0 8px;
    font-size: 22px;
  }
}

.review-note {
  margin-bottom: 18px;
}

.rating-cell {
  display: flex;
  align-items: center;
  gap: 10px;

  span {
    color: #8d98b5;
  }
}

.review-detail-stack {
  display: grid;
  gap: 14px;
}

.review-detail-card {
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

.review-detail-card--content {
  p {
    white-space: pre-wrap;
  }
}

.pagination-wrap {
  justify-content: flex-end;
  margin-top: 22px;
}
</style>
