<template>
  <div class="page-shell activity-page">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>活动管理</h3>
            <p>维护优惠活动的时间、折扣、投放范围与封面图。</p>
          </div>
          <div class="toolbar-actions">
            <el-input v-model="query.keyword" clearable placeholder="活动标题关键词" style="width: 240px" @clear="handleFilterChange" @input="handleKeywordInput" @keyup.enter="handleSearch" />
            <el-select v-model="query.status" clearable placeholder="状态" style="width: 140px" @change="handleFilterChange">
              <el-option label="启用" :value="1" />
              <el-option label="禁用" :value="0" />
            </el-select>
            <el-button type="primary" :loading="loading" :disabled="loading" @click="handleSearch">查询</el-button>
            <el-button :disabled="loading" @click="resetFilters">重置</el-button>
            <el-button type="primary" :disabled="loading || submitting" @click="openCreate">新增活动</el-button>
          </div>
        </div>
      </template>

      <div class="activity-summary">
        <div class="activity-summary__hero">
          <span>活动总数</span>
          <strong>{{ filteredList.length }}</strong>
          <p>当前筛选结果</p>
        </div>
        <div class="activity-summary__stats">
          <div class="activity-summary__card">
            <span>启用中</span>
            <strong>{{ enabledCount }}</strong>
            <p>前台可见活动</p>
          </div>
          <div class="activity-summary__card">
            <span>进行中</span>
            <strong>{{ activeCount }}</strong>
            <p>当前时间命中活动周期</p>
          </div>
          <div class="activity-summary__card">
            <span>即将结束</span>
            <strong>{{ endingSoonCount }}</strong>
            <p>48 小时内结束</p>
          </div>
        </div>
      </div>

      <div class="activity-context" v-if="query.keyword || query.status !== undefined">
        <el-tag v-if="query.keyword" effect="dark" round>关键词：{{ query.keyword }}</el-tag>
        <el-tag v-if="query.status !== undefined" type="success" round>{{ Number(query.status) === 1 ? '仅看启用' : '仅看禁用' }}</el-tag>
        <el-button link @click="resetFilters">清空筛选</el-button>
      </div>

      <el-table :data="filteredList" v-loading="loading" row-key="activity_id" empty-text="当前没有符合条件的活动，试试重置筛选或新建一个活动。">
        <el-table-column prop="activity_id" label="活动 ID" min-width="100" />
        <el-table-column label="活动信息" min-width="280">
          <template #default="{ row }">
            <div class="activity-cell">
              <el-image v-if="buildAssetUrl(row.image)" :src="buildAssetUrl(row.image)" class="activity-cover" fit="cover" preview-teleported />
              <div v-else class="activity-cover activity-cover--placeholder">ACT</div>
              <div>
                <strong>{{ row.title || '-' }}</strong>
                <p>{{ row.description || '暂无描述' }}</p>
                <span>{{ formatActivityType(row.activity_type) }} / {{ formatDiscount(row) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="投放范围" min-width="220">
          <template #default="{ row }">
            菜品 {{ formatIdList(row.target_dish_ids) }}<br />
            档口 {{ formatIdList(row.target_canteen_ids) }}
          </template>
        </el-table-column>
        <el-table-column label="活动时间" min-width="220">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}<br />
            {{ formatDateTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="120">
          <template #default="{ row }">
            <el-switch :model-value="normalizeStatus(row.status)" :loading="togglingId === row.activity_id" :disabled="submitting || deletingId === row.activity_id" inline-prompt active-text="启用" inactive-text="禁用" @change="toggleStatus(row, $event)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="220">
          <template #default="{ row }">
            <el-space wrap>
              <el-button size="small" :disabled="submitting || deletingId === row.activity_id" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" :disabled="submitting" @click="copySummary(row)">复制</el-button>
              <el-button size="small" type="danger" plain :loading="deletingId === row.activity_id" :disabled="submitting || togglingId === row.activity_id" @click="removeActivity(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="currentId ? '编辑活动' : '新增活动'" width="760px" @closed="handleClosed">
      <el-form ref="formRef" label-width="110px" :model="form" :rules="rules">
        <el-form-item label="活动标题" prop="title">
          <el-input v-model="form.title" maxlength="60" show-word-limit />
        </el-form-item>
        <el-form-item label="活动描述">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="300" show-word-limit />
        </el-form-item>
        <el-form-item label="活动类型" prop="activity_type">
          <el-select v-model="form.activity_type" style="width: 100%">
            <el-option label="折扣活动" value="discount" />
            <el-option label="秒杀活动" value="seckill" />
            <el-option label="套餐活动" value="package" />
            <el-option label="其他活动" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="优惠类型" prop="discount_type">
          <el-select v-model="form.discount_type" style="width: 100%">
            <el-option label="折扣百分比" value="percentage" />
            <el-option label="固定减免" value="fixed" />
          </el-select>
        </el-form-item>
        <el-form-item label="优惠值" prop="discount_value">
          <el-input-number v-model="form.discount_value" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="菜品 ID 列表">
          <el-input v-model="dishIdsInput" placeholder="例如：1,2,3" />
        </el-form-item>
        <el-form-item label="档口 ID 列表">
          <el-input v-model="canteenIdsInput" placeholder="例如：136,137" />
        </el-form-item>
        <el-form-item label="活动封面">
          <el-upload action="#" :auto-upload="false" :show-file-list="false" accept="image/png,image/jpeg,image/jpg,image/gif,image/webp" :disabled="submitting" :on-change="handleImageChange" :on-remove="clearImageSelection">
            <el-button :disabled="submitting">选择图片</el-button>
          </el-upload>
          <div class="upload-tip">仅支持 JPG / PNG / GIF / WEBP，大小不超过 5MB。保存时自动上传选中的封面图；若上传失败，将保留活动基础信息并提示你重新上传。</div>
          <div class="upload-meta" v-if="imageMetaName || imageStatusText">
            <span v-if="imageMetaName">已选择：{{ imageMetaName }}</span>
            <el-tag v-if="imageStatusText" :type="imageStatusType" size="small" effect="plain">{{ imageStatusText }}</el-tag>
            <el-button v-if="imageMetaName" link type="danger" :disabled="submitting" @click="clearImageSelection">移除</el-button>
          </div>
          <el-image v-if="imagePreview" :src="imagePreview" class="dialog-cover-preview" fit="cover" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="submitting" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="submitDisabled" @click="submitForm">{{ currentId ? '保存并同步' : '创建并同步' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { activityApi } from '@/api/modules/activities'
import { ASSET_BASE_URL } from '@/utils/constants'
import { formatDateTime } from '@/utils/formatters'

const IMAGE_MAX_SIZE = 5 * 1024 * 1024
const IMAGE_ACCEPTED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const currentId = ref(null)
const formRef = ref(null)
const list = ref([])
const imageFile = ref(null)
const imagePreview = ref('')
const imageMetaName = ref('')
const previewObjectUrl = ref('')
const deletingId = ref(null)
const togglingId = ref(null)
const searchTimer = ref(null)
const dishIdsInput = ref('')
const canteenIdsInput = ref('')
const query = reactive({ keyword: '', status: undefined })
const form = reactive({
  title: '',
  description: '',
  activity_type: 'discount',
  discount_type: 'percentage',
  discount_value: 0,
  start_time: '',
  end_time: '',
  target_dish_ids: [],
  target_canteen_ids: [],
  image: '',
  status: 1
})

const rules = {
  title: [{ required: true, message: '请输入活动标题', trigger: 'blur' }],
  activity_type: [{ required: true, message: '请选择活动类型', trigger: 'change' }],
  discount_type: [{ required: true, message: '请选择优惠类型', trigger: 'change' }],
  discount_value: [{ required: true, message: '请输入优惠值', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    {
      validator: (_rule, value, callback) => {
        if (!value || !form.start_time) {
          callback()
          return
        }
        if (new Date(value).getTime() <= new Date(form.start_time).getTime()) {
          callback(new Error('结束时间必须晚于开始时间'))
          return
        }
        callback()
      },
      trigger: 'change'
    }
  ]
}

const normalizeStatus = (value) => Number(value) === 1 || value === true
const normalizeAssetPath = (path) => {
  if (!path) return ''
  const normalized = String(path).replace(/\\/g, '/').trim()
  return normalized.replace(/^uploads\/+/, '').replace(/^\/+/, '')
}

const buildAssetUrl = (path) => {
  if (!path) return ''
  if (/^blob:/.test(path) || /^https?:\/\//.test(path)) return path
  const normalizedPath = normalizeAssetPath(path)
  if (!normalizedPath) return ''
  return `${ASSET_BASE_URL}/uploads/${normalizedPath}`
}
const formatActivityType = (value) => ({ discount: '折扣活动', seckill: '秒杀活动', package: '套餐活动', other: '其他活动' }[value] || value || '未分类')
const formatDiscount = (row) => row.discount_type === 'fixed' ? `减免 ¥${Number(row.discount_value || 0).toFixed(2)}` : `${Number(row.discount_value || 0)}% 折扣`
const formatIdList = (value) => Array.isArray(value) && value.length ? value.join(', ') : '全部'
const imageStatusText = computed(() => {
  if (imageMetaName.value) return '待上传'
  if (form.image) return '已同步封面'
  return ''
})
const imageStatusType = computed(() => imageMetaName.value ? 'warning' : 'success')
const submitDisabled = computed(() => submitting.value || loading.value)

const filteredList = computed(() => list.value.filter((item) => {
  const keywordMatched = !query.keyword || String(item.title || '').includes(query.keyword.trim())
  const statusMatched = query.status === undefined || Number(item.status) === Number(query.status)
  return keywordMatched && statusMatched
}))

const enabledCount = computed(() => filteredList.value.filter((item) => normalizeStatus(item.status)).length)
const activeCount = computed(() => {
  const now = Date.now()
  return filteredList.value.filter((item) => normalizeStatus(item.status) && new Date(item.start_time).getTime() <= now && new Date(item.end_time).getTime() >= now).length
})
const endingSoonCount = computed(() => {
  const now = Date.now()
  const twoDays = 48 * 60 * 60 * 1000
  return filteredList.value.filter((item) => {
    const end = new Date(item.end_time).getTime()
    return end >= now && end - now <= twoDays
  }).length
})

const parseIdInput = (value) => value.split(',').map((item) => Number(item.trim())).filter((item) => Number.isFinite(item) && item > 0)
const revokePreviewUrl = () => {
  if (previewObjectUrl.value) {
    URL.revokeObjectURL(previewObjectUrl.value)
    previewObjectUrl.value = ''
  }
}
const clearSearchTimer = () => {
  if (searchTimer.value) {
    window.clearTimeout(searchTimer.value)
    searchTimer.value = null
  }
}
const clearImageSelection = () => {
  imageFile.value = null
  imageMetaName.value = ''
  revokePreviewUrl()
  imagePreview.value = form.image ? buildAssetUrl(form.image) : ''
}
const resetUpload = () => {
  imageFile.value = null
  imageMetaName.value = ''
  revokePreviewUrl()
  imagePreview.value = ''
}
const resetForm = () => {
  currentId.value = null
  Object.assign(form, {
    title: '',
    description: '',
    activity_type: 'discount',
    discount_type: 'percentage',
    discount_value: 0,
    start_time: '',
    end_time: '',
    target_dish_ids: [],
    target_canteen_ids: [],
    image: '',
    status: 1
  })
  dishIdsInput.value = ''
  canteenIdsInput.value = ''
  resetUpload()
}

const loadData = async () => {
  loading.value = true
  try {
    list.value = await activityApi.getList()
  } catch (error) {
    ElMessage.error(error?.message || '加载活动列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  clearSearchTimer()
  query.keyword = query.keyword.trim()
}
const handleKeywordInput = () => {
  clearSearchTimer()
  searchTimer.value = window.setTimeout(() => {
    query.keyword = query.keyword.trim()
  }, 300)
}
const handleFilterChange = () => {
  clearSearchTimer()
  query.keyword = query.keyword.trim()
}
const resetFilters = () => {
  clearSearchTimer()
  query.keyword = ''
  query.status = undefined
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}
const openEdit = (row) => {
  currentId.value = row.activity_id
  Object.assign(form, {
    title: row.title || '',
    description: row.description || '',
    activity_type: row.activity_type || 'discount',
    discount_type: row.discount_type || 'percentage',
    discount_value: Number(row.discount_value || 0),
    start_time: row.start_time || '',
    end_time: row.end_time || '',
    target_dish_ids: row.target_dish_ids || [],
    target_canteen_ids: row.target_canteen_ids || [],
    image: row.image || '',
    status: Number(row.status ?? 1)
  })
  dishIdsInput.value = Array.isArray(row.target_dish_ids) ? row.target_dish_ids.join(',') : ''
  canteenIdsInput.value = Array.isArray(row.target_canteen_ids) ? row.target_canteen_ids.join(',') : ''
  imageMetaName.value = ''
  revokePreviewUrl()
  imagePreview.value = buildAssetUrl(row.image)
  imageFile.value = null
  dialogVisible.value = true
}
const handleClosed = () => {
  formRef.value?.resetFields()
  formRef.value?.clearValidate()
  resetForm()
}

const handleImageChange = (file) => {
  const raw = file.raw || null
  if (!raw) return
  if (!IMAGE_ACCEPTED_TYPES.includes(raw.type)) {
    ElMessage.warning('仅支持 JPG / PNG / GIF / WEBP 格式图片')
    clearImageSelection()
    return
  }
  if (raw.size > IMAGE_MAX_SIZE) {
    ElMessage.warning('图片不能超过 5MB，请压缩后再上传')
    clearImageSelection()
    return
  }
  imageFile.value = raw
  imageMetaName.value = raw?.name || file.name || ''
  revokePreviewUrl()
  previewObjectUrl.value = URL.createObjectURL(raw)
  imagePreview.value = previewObjectUrl.value || buildAssetUrl(form.image)
}

const submitForm = async () => {
  if (submitting.value) return
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请先完善活动信息后再保存')
    return
  }

  submitting.value = true
  const isEdit = Boolean(currentId.value)
  try {
    form.target_dish_ids = parseIdInput(dishIdsInput.value)
    form.target_canteen_ids = parseIdInput(canteenIdsInput.value)
    const payload = { ...form }
    let saved = null
    if (isEdit) {
      saved = await activityApi.update(currentId.value, payload)
    } else {
      saved = await activityApi.create(payload)
      currentId.value = saved?.activity_id || null
    }

    if (imageFile.value && currentId.value) {
      try {
        const uploadResult = await activityApi.uploadImage(imageFile.value, currentId.value)
        form.image = uploadResult?.path || form.image
        imagePreview.value = buildAssetUrl(uploadResult?.path || form.image)
        imageMetaName.value = ''
        imageFile.value = null
        revokePreviewUrl()
        ElMessage.success(isEdit ? '活动已保存，封面已更新' : '活动已创建，封面已上传')
      } catch (_error) {
        const latestId = currentId.value
        const fallbackPreview = form.image ? buildAssetUrl(form.image) : ''
        imagePreview.value = fallbackPreview
        ElMessage.warning(`活动基础信息已保存，但封面上传失败，请重新上传后再保存。${latestId ? ` 活动 ID：${latestId}` : ''}`)
      }
    } else {
      ElMessage.success(isEdit ? '活动已保存' : '活动已创建')
    }

    await loadData()
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存活动失败')
  } finally {
    submitting.value = false
  }
}

const toggleStatus = async (row, enabled) => {
  if (togglingId.value || deletingId.value) return
  const previousStatus = row.status
  row.status = enabled ? 1 : 0
  togglingId.value = row.activity_id
  try {
    await activityApi.updateStatus(row.activity_id, row.status)
    ElMessage.success(enabled ? '活动已启用' : '活动已禁用')
  } catch (error) {
    row.status = previousStatus
    ElMessage.error(error?.message || '更新活动状态失败')
  } finally {
    togglingId.value = null
  }
}

const copySummary = async (row) => {
  const summary = [
    `活动：${row.title || '-'}`,
    `类型：${formatActivityType(row.activity_type)}`,
    `优惠：${formatDiscount(row)}`,
    `时间：${formatDateTime(row.start_time)} ~ ${formatDateTime(row.end_time)}`
  ].join('\n')
  try {
    await navigator.clipboard.writeText(summary)
    ElMessage.success('活动摘要已复制')
  } catch (_error) {
    ElMessage.warning('当前环境不支持复制')
  }
}

const removeActivity = async (row) => {
  if (deletingId.value) return
  try {
    await ElMessageBox.confirm(`确认删除活动「${row.title || row.activity_id}」吗？`, '删除活动', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除活动')
    return
  }

  deletingId.value = row.activity_id
  const backup = [...list.value]
  list.value = list.value.filter((item) => item.activity_id !== row.activity_id)
  try {
    await activityApi.remove(row.activity_id)
    ElMessage.success('活动已删除')
  } catch (error) {
    list.value = backup
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除活动失败')
  } finally {
    deletingId.value = null
  }
}

onMounted(loadData)
onBeforeUnmount(() => {
  clearSearchTimer()
  revokePreviewUrl()
})
</script>

<style scoped lang="scss">
.activity-page {
  display: grid;
  gap: 20px;
}

.activity-summary {
  display: grid;
  grid-template-columns: minmax(220px, 1.1fr) minmax(0, 2fr);
  gap: 18px;
  margin-bottom: 18px;
}

.activity-summary__hero,
.activity-summary__card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  background: rgba(255, 255, 255, 0.03);
}

.activity-summary__hero {
  span,
  p {
    color: #8d98b5;
  }

  strong {
    display: block;
    margin: 10px 0 8px;
    font-size: 34px;
  }
}

.activity-summary__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.activity-summary__card {
  span,
  p {
    color: #8d98b5;
  }

  strong {
    display: block;
    margin: 10px 0 8px;
    font-size: 24px;
  }
}

.activity-cell {
  display: flex;
  align-items: center;
  gap: 14px;

  p,
  span {
    margin: 6px 0 0;
    color: #8d98b5;
    font-size: 13px;
  }
}

.activity-cover {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  flex-shrink: 0;
}

.activity-cover--placeholder {
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(36, 201, 154, 0.3), rgba(110, 168, 254, 0.34));
  color: #fff;
  font-weight: 700;
}

.upload-tip {
  margin-top: 10px;
  color: #8d98b5;
  font-size: 13px;
}

.upload-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  color: #c7d2e8;
  font-size: 13px;
}

.activity-context {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.dialog-cover-preview {
  display: block;
  width: 180px;
  height: 110px;
  margin-top: 14px;
  border-radius: 18px;
}
</style>

