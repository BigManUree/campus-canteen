<template>
  <div class="page-shell category-page">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>分类管理</h3>
            <p>当前接口返回全部分类列表，此页按前端树形整理父子关系并提供名称筛选。</p>
          </div>
          <div class="toolbar-actions">
            <el-input v-model="query.keyword" clearable placeholder="分类名称关键词" style="width: 240px" @clear="handleFilterChange" @keyup.enter="handleSearch" />
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
            <el-button type="primary" @click="openCreate">新增分类</el-button>
          </div>
        </div>
      </template>

      <div class="category-summary">
        <div class="category-summary__card category-summary__card--hero">
          <span>分类总数</span>
          <strong>{{ rawList.length }}</strong>
          <p>接口返回的全部分类条目</p>
        </div>
        <div class="category-summary__card">
          <span>顶级分类</span>
          <strong>{{ rootCount }}</strong>
          <p>父级 ID 为 0 或空的分类</p>
        </div>
        <div class="category-summary__card">
          <span>子级分类</span>
          <strong>{{ childCount }}</strong>
          <p>已挂载到父级下的分类</p>
        </div>
        <div class="category-summary__card">
          <span>当前筛选</span>
          <strong>{{ filteredCount }}</strong>
          <p>按关键词命中的可见分类数</p>
        </div>
      </div>

      <el-table :data="tableData" v-loading="loading" row-key="category_id" default-expand-all>
        <el-table-column prop="category_name" label="分类名称" min-width="220" />
        <el-table-column label="层级" min-width="120">
          <template #default="{ row }">
            <el-tag :type="Number(row.parent_id || 0) > 0 ? 'info' : 'success'">{{ Number(row.parent_id || 0) > 0 ? '子级分类' : '顶级分类' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category_id" label="分类 ID" min-width="100" />
        <el-table-column prop="parent_id" label="父级 ID" min-width="100" />
        <el-table-column prop="sort_order" label="排序" min-width="100" />
        <el-table-column label="创建时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="180">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeCategory(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="currentId ? '编辑分类' : '新增分类'" width="460px" @closed="handleClosed">
      <el-form ref="formRef" label-width="88px" :model="form" :rules="rules">
        <el-form-item label="分类名称" prop="category_name">
          <el-input v-model="form.category_name" />
        </el-form-item>
        <el-form-item label="父级分类" prop="parent_id">
          <el-select v-model="form.parent_id" style="width: 100%">
            <el-option label="作为顶级分类" :value="0" />
            <el-option v-for="item in parentOptions" :key="item.category_id" :label="item.category_name" :value="Number(item.category_id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序值" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi } from '@/api/modules/categories'
import { formatDateTime } from '@/utils/formatters'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const currentId = ref(null)
const formRef = ref(null)
const rawList = ref([])
const query = reactive({ keyword: '' })
const form = reactive({ category_name: '', parent_id: 0, sort_order: 0 })

const rules = {
  category_name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
  sort_order: [{ required: true, message: '请输入排序值', trigger: 'change' }]
}

const keyword = computed(() => query.keyword.trim())

const buildTree = (items) => {
  const map = new Map()
  items.forEach((item) => {
    map.set(item.category_id, { ...item, children: [] })
  })

  const roots = []
  map.forEach((item) => {
    const parentId = Number(item.parent_id || 0)
    const parent = map.get(parentId)
    if (parent && parentId !== Number(item.category_id)) {
      parent.children.push(item)
    } else {
      roots.push(item)
    }
  })

  const sortItems = (nodes) => nodes
    .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0) || Number(a.category_id || 0) - Number(b.category_id || 0))
    .map((item) => ({
      ...item,
      children: sortItems(item.children || [])
    }))

  return sortItems(roots)
}

const filterTree = (nodes, currentKeyword) => {
  if (!currentKeyword) return nodes
  return nodes.reduce((acc, node) => {
    const children = filterTree(node.children || [], currentKeyword)
    const selfMatched = String(node.category_name || '').includes(currentKeyword)
    if (selfMatched || children.length) {
      acc.push({
        ...node,
        children
      })
    }
    return acc
  }, [])
}

const countNodes = (nodes) => nodes.reduce((sum, item) => sum + 1 + countNodes(item.children || []), 0)

const treeData = computed(() => buildTree(rawList.value))
const tableData = computed(() => filterTree(treeData.value, keyword.value))
const filteredCount = computed(() => countNodes(tableData.value))
const rootCount = computed(() => rawList.value.filter((item) => !Number(item.parent_id || 0)).length)
const childCount = computed(() => Math.max(rawList.value.length - rootCount.value, 0))
const parentOptions = computed(() => rawList.value.filter((item) => Number(item.parent_id || 0) === 0 && Number(item.category_id) !== Number(currentId.value)))

const loadData = async () => {
  loading.value = true
  try {
    const result = await categoryApi.getList()
    rawList.value = Array.isArray(result) ? result : result?.items || result?.data || []
  } catch (error) {
    ElMessage.error(error?.message || '加载分类列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.keyword = query.keyword.trim()
}

const handleFilterChange = () => {
  query.keyword = query.keyword.trim()
}

const resetFilters = () => {
  query.keyword = ''
}

const resetForm = () => {
  currentId.value = null
  Object.assign(form, { category_name: '', parent_id: 0, sort_order: 0 })
}

const handleClosed = () => {
  formRef.value?.resetFields()
  formRef.value?.clearValidate()
  resetForm()
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const openEdit = async (row) => {
  currentId.value = row.category_id
  try {
    const detailResponse = await categoryApi.getDetail(row.category_id)
    const detail = detailResponse?.data || detailResponse
    Object.assign(form, {
      category_name: detail.category_name || '',
      parent_id: Number(detail.parent_id || 0),
      sort_order: Number(detail.sort_order || 0)
    })
  } catch (_error) {
    Object.assign(form, {
      category_name: row.category_name || '',
      parent_id: Number(row.parent_id || 0),
      sort_order: Number(row.sort_order || 0)
    })
    ElMessage.warning('分类详情加载失败，已使用列表数据填充')
  }
  dialogVisible.value = true
}

const submitForm = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请先完善分类信息后再保存')
    return
  }

  submitting.value = true
  try {
    const payload = { ...form }
    if (currentId.value) {
      await categoryApi.update(currentId.value, payload)
      ElMessage.success('分类已更新')
    } else {
      await categoryApi.create(payload)
      ElMessage.success('分类已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存分类失败')
  } finally {
    submitting.value = false
  }
}

const removeCategory = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除分类「${row.category_name}」吗？`, '删除分类', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除分类')
    return
  }

  try {
    await categoryApi.remove(row.category_id)
    ElMessage.success('分类已删除')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除分类失败')
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.category-page {
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

.toolbar-actions {
  display: flex;
  gap: 12px;
}

.category-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.category-summary__card {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(151, 164, 199, 0.14);
  background: rgba(255, 255, 255, 0.03);

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

.category-summary__card--hero strong {
  font-size: 34px;
}
</style>
