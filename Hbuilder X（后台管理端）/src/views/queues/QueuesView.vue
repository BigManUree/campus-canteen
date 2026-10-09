<template>
  <div class="page-shell queue-page">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>排队看板</h3>
            <p>查看并更新档口排队人数、预计等待时间与当前排队状态。</p>
          </div>
          <el-button text @click="resetPanel">重置面板</el-button>
        </div>
      </template>

      <div class="queue-overview">
        <div class="queue-overview__search">
          <el-form ref="searchFormRef" inline :model="searchForm" :rules="searchRules">
            <el-form-item label="档口 ID" prop="canteen_id">
              <el-input v-model="searchForm.canteen_id" placeholder="请输入档口 ID" style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadQueue">查询排队信息</el-button>
        </el-form-item>
      </el-form>
        </div>

        <div class="queue-overview__tips">
          <div class="queue-tip-card">
            <span>当前状态</span>
            <strong>{{ queueStatusText }}</strong>
          </div>
          <div class="queue-tip-card">
            <span>拥挤指数</span>
            <strong>{{ queuePressureLabel }}</strong>
          </div>
          <div class="queue-tip-card">
            <span>预计恢复节奏</span>
            <strong>{{ recoveryAdvice }}</strong>
          </div>
        </div>
      </div>

      <div v-if="queueInfo" class="queue-panel">
        <div class="queue-stat">
          <span>当前排队人数</span>
          <strong>{{ queueInfo.current_queue_number || 0 }}</strong>
        </div>
        <div class="queue-stat">
          <span>预计等待时间</span>
          <strong>{{ queueInfo.estimated_wait_time || 0 }} 分钟</strong>
        </div>
        <div class="queue-stat queue-stat--accent">
          <span>队列状态</span>
          <strong>{{ queueInfo.status || 'normal' }}</strong>
          <p>{{ recoveryAdvice }}</p>
        </div>
      </div>

      <el-form v-if="queueInfo" ref="queueFormRef" label-width="110px" :model="form" :rules="queueRules" class="queue-form">
        <el-form-item label="排队人数" prop="current_queue_number">
          <el-input-number v-model="form.current_queue_number" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="等待时间" prop="estimated_wait_time">
          <el-input-number v-model="form.estimated_wait_time" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="队列状态" prop="status">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="正常" value="normal" />
            <el-option label="拥挤" value="busy" />
            <el-option label="暂停" value="paused" />
          </el-select>
        </el-form-item>
        <div class="queue-form__actions">
        <el-button type="success" :loading="submitting" @click="submitUpdate">更新排队信息</el-button>
          <el-button @click="syncFromLoaded">恢复当前查询值</el-button>
        </div>
      </el-form>

      <el-empty v-if="!queueInfo && !loading" description="请输入档口 ID 查询排队信息" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { queueApi } from '@/api/modules/queues'

const searchFormRef = ref(null)
const queueFormRef = ref(null)
const searchForm = reactive({ canteen_id: '' })
const queueInfo = ref(null)
const loading = ref(false)
const submitting = ref(false)
const form = reactive({ current_queue_number: 0, estimated_wait_time: 0, status: 'normal' })

const searchRules = {
  canteen_id: [{ required: true, message: '请输入档口 ID', trigger: 'blur' }]
}

const queueRules = {
  current_queue_number: [
    { required: true, message: '请输入排队人数', trigger: 'change' },
    { type: 'number', min: 0, max: 999, message: '排队人数需在 0 到 999 之间', trigger: 'change' }
  ],
  estimated_wait_time: [
    { required: true, message: '请输入等待时间', trigger: 'change' },
    { type: 'number', min: 0, max: 300, message: '等待时间需在 0 到 300 分钟之间', trigger: 'change' }
  ],
  status: [{ required: true, message: '请选择队列状态', trigger: 'change' }]
}

const queueStatusText = computed(() => {
  if (!queueInfo.value) return '待查询'
  if (form.status === 'paused') return '暂停接单'
  if (form.status === 'busy' || form.current_queue_number >= 30 || form.estimated_wait_time >= 30) return '高峰拥挤'
  if (form.current_queue_number >= 15 || form.estimated_wait_time >= 15) return '排队较多'
  return '排队平稳'
})

const queuePressureLabel = computed(() => {
  if (!queueInfo.value) return '暂无数据'
  if (form.status === 'paused') return '建议先处理积压订单'
  if (form.current_queue_number >= 30 || form.estimated_wait_time >= 30) return '建议增加出餐人手'
  if (form.current_queue_number >= 15 || form.estimated_wait_time >= 15) return '建议关注现场节奏'
  return '当前可正常接单'
})

const recoveryAdvice = computed(() => {
  if (!queueInfo.value) return '查询后显示建议'
  if (form.status === 'paused') return '建议暂停新增高峰促销，优先恢复出餐效率。'
  if (form.estimated_wait_time >= 30) return '建议引导错峰取餐，并检查制作瓶颈。'
  if (form.estimated_wait_time >= 15) return '建议适度提醒用户等待时长。'
  return '等待时长可控，可保持当前处理节奏。'
})

const applyQueueResult = (result) => {
  queueInfo.value = result || {}
  Object.assign(form, {
    current_queue_number: Number(result?.current_queue_number || 0),
    estimated_wait_time: Number(result?.estimated_wait_time || 0),
    status: result?.status || 'normal'
  })
}

const loadQueue = async () => {
  try {
    await searchFormRef.value?.validate()
  } catch {
    ElMessage.warning('请先输入档口 ID 后再查询')
    return
  }
  loading.value = true
  try {
    const result = await queueApi.getInfo(searchForm.canteen_id)
    applyQueueResult(result)
    ElMessage.success('排队信息已加载')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载排队信息失败')
  } finally {
    loading.value = false
  }
}

const submitUpdate = async () => {
  try {
    await queueFormRef.value?.validate()
  } catch {
    ElMessage.warning('请先完善排队信息后再提交')
    return
  }
  submitting.value = true
  try {
    await queueApi.update(searchForm.canteen_id, { ...form })
    ElMessage.success('排队信息已更新')
    const latest = await queueApi.getInfo(searchForm.canteen_id)
    applyQueueResult(latest)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '更新排队信息失败')
  } finally {
    submitting.value = false
  }
}

const syncFromLoaded = () => {
  if (!queueInfo.value) {
    ElMessage.info('当前没有已加载的排队信息')
    return
  }
  applyQueueResult(queueInfo.value)
  queueFormRef.value?.clearValidate()
  ElMessage.success('已恢复当前查询值')
}

const resetPanel = () => {
  searchForm.canteen_id = ''
  queueInfo.value = null
  Object.assign(form, { current_queue_number: 0, estimated_wait_time: 0, status: 'normal' })
  searchFormRef.value?.clearValidate()
  queueFormRef.value?.clearValidate()
  ElMessage.success('排队面板已重置')
}
</script>

<style scoped lang="scss">
.queue-page,
.queue-overview,
.queue-overview__tips,
.queue-panel {
  display: grid;
  gap: 18px;
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

.queue-overview {
  grid-template-columns: minmax(260px, 1.15fr) minmax(0, 1fr);
}

.queue-overview__search,
.queue-tip-card,
.queue-stat {
  padding: 20px;
  border-radius: 20px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  background: rgba(255, 255, 255, 0.03);
}

.queue-overview__tips {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.queue-tip-card {
  span {
    display: block;
    margin-bottom: 10px;
    color: #90a0c0;
  }

  strong {
    font-size: 18px;
    line-height: 1.6;
  }
}

.queue-panel {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 6px;
}

.queue-stat {
  span {
    display: block;
    margin-bottom: 10px;
    color: #90a0c0;
  }

  strong {
    font-size: 28px;
  }

  p {
    margin: 10px 0 0;
    color: #8d98b5;
    line-height: 1.7;
  }
}

.queue-stat--accent {
  background: linear-gradient(135deg, rgba(110, 168, 254, 0.12), rgba(99, 230, 190, 0.12));
}

.queue-form {
  max-width: 520px;

  &__actions {
    display: flex;
    gap: 12px;
  }
}
</style>
