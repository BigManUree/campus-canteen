<template>
  <div class="page-shell page-stack">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>菜品管理</h3>
            <p>管理菜品资料、价格库存和上下架状态。</p>
          </div>
          <div class="toolbar-actions">
            <el-input v-model="query.keyword" clearable placeholder="菜品名 / 档口名" style="width: 240px" @clear="handleFilterChange" @keyup.enter="handleSearch" />
            <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
            <el-button type="primary" @click="openCreate">新增菜品</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" row-key="dish_id">
        <el-table-column prop="dish_id" label="菜品 ID" min-width="100" />
        <el-table-column prop="name" label="菜品名称" min-width="180" />
        <el-table-column label="所属分类" min-width="160">
          <template #default="{ row }">{{ getCategoryLabel(row.category_id) }}</template>
        </el-table-column>
        <el-table-column label="菜品图片" min-width="180">
          <template #default="{ row }">
            <div v-if="getImagePreviewList(row).length" class="image-preview-list">
              <el-image
                v-for="(image, index) in getImagePreviewList(row).slice(0, 3)"
                :key="`${row.dish_id}-${index}`"
                :src="image"
                class="dish-thumb"
                fit="cover"
                :preview-src-list="getImagePreviewList(row)"
                preview-teleported
                hide-on-click-modal
              />
              <span v-if="getImagePreviewList(row).length > 3" class="image-more">+{{ getImagePreviewList(row).length - 3 }}</span>
            </div>
            <el-text v-else type="info">暂无图片</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="canteen_name" label="所属档口" min-width="160" />
        <el-table-column label="价格" min-width="110">
          <template #default="{ row }">¥{{ currency(row.price) }}</template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" min-width="100" />
        <el-table-column label="状态" min-width="120">
          <template #default="{ row }">
            <el-switch
              :model-value="normalizeStatus(row.status)"
              inline-prompt
              active-text="上架"
              inactive-text="下架"
              @change="toggleStatus(row, $event)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="240" show-overflow-tooltip />
        <el-table-column label="操作" fixed="right" min-width="200">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeDish(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="currentId ? '编辑菜品' : '新增菜品'" width="680px" @closed="handleClosed">
      <el-form ref="formRef" label-width="92px" :model="form" :rules="rules">
        <el-form-item label="菜品名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="库存" prop="stock">
          <el-input-number v-model="form.stock" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="form.category_id" filterable placeholder="请选择分类" style="width: 100%" :loading="optionLoading">
            <el-option v-for="item in categoryOptions" :key="item.category_id" :label="item.category_name" :value="Number(item.category_id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="档口" prop="canteen_id">
          <el-select v-model="form.canteen_id" filterable placeholder="请选择档口" style="width: 100%" :loading="optionLoading">
            <el-option v-for="item in canteenOptions" :key="item.canteen_id" :label="item.canteen_name" :value="Number(item.canteen_id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="菜品图片">
          <el-upload
            action="#"
            list-type="picture-card"
            :auto-upload="false"
            :file-list="uploadFileList"
            :limit="9"
            accept="image/*"
            multiple
            :on-change="handleUploadChange"
            :on-remove="handleUploadRemove"
            :on-preview="handlePicturePreview"
            :on-exceed="handleUploadExceed"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持最多 9 张图片；保存时会自动上传新增图片。</div>
        </el-form-item>
        <el-form-item label="菜品描述">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewVisible" title="图片预览" width="720px">
      <img v-if="previewUrl" :src="previewUrl" alt="preview" class="dialog-preview-image" />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { canteenApi } from '@/api/modules/canteens'
import { categoryApi } from '@/api/modules/categories'
import { dishApi } from '@/api/modules/dishes'
import { ASSET_BASE_URL } from '@/utils/constants'
import { currency, normalizeListPayload } from '@/utils/formatters'

const MAX_IMAGE_COUNT = 9

const loading = ref(false)
const submitting = ref(false)
const optionLoading = ref(false)
const dialogVisible = ref(false)
const currentId = ref(null)
const formRef = ref(null)
const list = ref([])
const categoryOptions = ref([])
const canteenOptions = ref([])
const previewVisible = ref(false)
const previewUrl = ref('')
const uploadFileList = ref([])
const query = reactive({ page: 1, page_size: 20, keyword: '' })
const form = reactive({
  name: '',
  price: 0,
  stock: 0,
  category_id: undefined,
  canteen_id: undefined,
  description: '',
  images: '[]'
})
const rules = {
  name: [{ required: true, message: '请输入菜品名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入菜品价格', trigger: 'change' }],
  stock: [{ required: true, message: '请输入菜品库存', trigger: 'change' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  canteen_id: [{ required: true, message: '请选择档口', trigger: 'change' }]
}

const categoryMap = computed(() => new Map(categoryOptions.value.map((item) => [Number(item.category_id), item.category_name])))
const canteenMap = computed(() => new Map(canteenOptions.value.map((item) => [Number(item.canteen_id), item.canteen_name])))

const normalizeAssetPath = (path) => {
  if (!path) return ''
  const normalized = String(path).replace(/\\/g, '/').trim()
  return normalized.replace(/^uploads\/+/, '').replace(/^\/+/, '')
}

const buildAssetUrl = (path) => {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  const normalizedPath = normalizeAssetPath(path)
  if (!normalizedPath) return ''
  return `${ASSET_BASE_URL}/uploads/${normalizedPath}`
}

const parseImages = (value) => {
  if (!value) return []
  if (Array.isArray(value)) return value.filter(Boolean)
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? parsed.filter(Boolean) : []
    } catch {
      return value ? [value] : []
    }
  }
  return []
}

const createUploadedFileItem = (path) => ({
  name: path.split('/').pop() || 'image',
  url: buildAssetUrl(path),
  status: 'success',
  responsePath: path,
  isUploaded: true
})

const syncFormImages = () => {
  const paths = uploadFileList.value
    .map((item) => item.responsePath)
    .filter(Boolean)
  form.images = JSON.stringify(paths)
}

const resetUploadState = () => {
  uploadFileList.value = []
  previewUrl.value = ''
  previewVisible.value = false
}

const normalizeStatus = (value) => value === 1 || value === true || value === 'on_sale'

const getImagePreviewList = (row) => parseImages(row.images).map((path) => buildAssetUrl(path))
const getCategoryLabel = (categoryId) => categoryMap.value.get(Number(categoryId)) || categoryId || '-'
const getCanteenLabel = (canteenId, row) => canteenMap.value.get(Number(canteenId)) || row.canteen_name || canteenId || '-'

const loadOptions = async () => {
  optionLoading.value = true
  try {
    const [categoryResult, canteenResult] = await Promise.all([
      categoryApi.getList(),
      canteenApi.getList({ page: 1, page_size: 100 })
    ])
    categoryOptions.value = Array.isArray(categoryResult) ? categoryResult : categoryResult?.items || categoryResult?.data || []
    canteenOptions.value = normalizeListPayload(canteenResult).items
  } catch (error) {
    ElMessage.error(error?.message || '加载筛选项失败')
  } finally {
    optionLoading.value = false
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const result = await dishApi.getList({ ...query })
    list.value = normalizeListPayload(result).items.map((item) => ({
      ...item,
      canteen_name: item.canteen_name || getCanteenLabel(item.canteen_id, item)
    }))
  } catch (error) {
    ElMessage.error(error?.message || '加载菜品列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.page = 1
  loadData()
}

const handleFilterChange = () => {
  if (query.page !== 1) {
    query.page = 1
    loadData()
  }
}

const resetFilters = () => {
  query.page = 1
  query.page_size = 20
  query.keyword = ''
  loadData()
}

const resetForm = () => {
  currentId.value = null
  Object.assign(form, { name: '', price: 0, stock: 0, category_id: undefined, canteen_id: undefined, description: '', images: '[]' })
  resetUploadState()
}

const openCreate = async () => {
  resetForm()
  try {
    if (!categoryOptions.value.length || !canteenOptions.value.length) {
      await loadOptions()
    }
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '打开新增菜品弹窗失败')
  }
}

const openEdit = async (row) => {
  try {
    if (!categoryOptions.value.length || !canteenOptions.value.length) {
      await loadOptions()
    }
    currentId.value = row.dish_id
    Object.assign(form, {
      name: row.name || '',
      price: Number(row.price || 0),
      stock: Number(row.stock || 0),
      category_id: row.category_id === null || row.category_id === undefined || row.category_id === '' ? undefined : Number(row.category_id),
      canteen_id: row.canteen_id === null || row.canteen_id === undefined || row.canteen_id === '' ? undefined : Number(row.canteen_id),
      description: row.description || '',
      images: typeof row.images === 'string' ? row.images : JSON.stringify(parseImages(row.images))
    })
    uploadFileList.value = parseImages(row.images).map(createUploadedFileItem)
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '打开菜品编辑弹窗失败')
  }
}

const handleClosed = () => {
  formRef.value?.resetFields()
  formRef.value?.clearValidate()
  resetForm()
}

const handleUploadChange = (_, fileList) => {
  uploadFileList.value = fileList.slice(0, MAX_IMAGE_COUNT)
  syncFormImages()
}

const handleUploadRemove = (_, fileList) => {
  uploadFileList.value = fileList
  syncFormImages()
}

const handleUploadExceed = () => {
  ElMessage.warning('最多只能上传 9 张图片')
}

const handlePicturePreview = (file) => {
  previewUrl.value = file.url || file.preview || ''
  previewVisible.value = true
}

const uploadPendingImages = async () => {
  const pendingFiles = uploadFileList.value.filter((item) => item.raw && !item.responsePath)
  if (!pendingFiles.length) {
    syncFormImages()
    return
  }

  const result = await dishApi.uploadImages(
    pendingFiles.map((item) => item.raw),
    currentId.value
  )
  const paths = result?.paths || []
  const urls = result?.urls || []

  pendingFiles.forEach((item, index) => {
    item.responsePath = paths[index] || ''
    item.url = buildAssetUrl(urls[index] || paths[index] || '')
    item.status = 'success'
    item.isUploaded = true
  })

  syncFormImages()
}

const submitForm = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请先完善菜品表单后再保存')
    return
  }

  submitting.value = true
  try {
    if (!currentId.value) {
      const created = await dishApi.create({ ...form })
      currentId.value = created?.dish_id || created?.data?.dish_id || null
    }

    await uploadPendingImages()
    const payload = { ...form }
    if (currentId.value) {
      await dishApi.update(currentId.value, payload)
      ElMessage.success('菜品已保存')
    }
    dialogVisible.value = false
    formRef.value?.resetFields()
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存菜品失败')
  } finally {
    submitting.value = false
  }
}

const toggleStatus = async (row, enabled) => {
  try {
    await dishApi.updateStatus(row.dish_id, { status: enabled ? 1 : 0 })
    ElMessage.success(enabled ? '菜品已上架' : '菜品已下架')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '更新菜品状态失败')
    await loadData()
  }
}

const removeDish = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除菜品「${row.name}」吗？`, '删除菜品', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除菜品')
    return
  }

  try {
    await dishApi.remove(row.dish_id)
    ElMessage.success('菜品已删除')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除菜品失败')
  }
}

onMounted(async () => {
  await Promise.all([loadOptions(), loadData()])
})
</script>

<style scoped lang="scss">
.page-stack {
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

.toolbar-actions {
  display: flex;
  gap: 12px;
}

.image-preview-list {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.dish-thumb {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.image-more {
  color: #8d98b5;
  font-size: 12px;
}

.upload-tip {
  font-size: 12px;
  color: #8d98b5;
  margin-top: 8px;
  line-height: 1.5;
}

.dialog-preview-image {
  display: block;
  width: 100%;
  max-height: 70vh;
  object-fit: contain;
}
</style>
