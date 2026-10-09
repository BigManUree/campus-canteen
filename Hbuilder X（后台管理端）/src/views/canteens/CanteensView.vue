<template>
  <div class="page-shell">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>档口管理</h3>
            <p>维护档口基础信息、服务方式、营业时间与联系资料。</p>
          </div>
          <div class="toolbar-actions">
            <el-input v-model="query.keyword" clearable placeholder="档口名称关键词" style="width: 240px" @clear="handleFilterChange" @keyup.enter="handleSearch" />
            <el-select v-model="query.status" clearable placeholder="状态" style="width: 140px" @change="handleFilterChange">
              <el-option label="启用" :value="1" />
              <el-option label="禁用" :value="0" />
            </el-select>
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
            <el-button type="primary" @click="openCreate">新增档口</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" row-key="canteen_id">
        <el-table-column prop="canteen_id" label="档口 ID" min-width="100" />
        <el-table-column prop="canteen_name" label="档口名称" min-width="180" />
        <el-table-column label="位置" min-width="220">
          <template #default="{ row }">{{ [row.building, row.floor, row.window_no].filter(Boolean).join(' / ') || '-' }}</template>
        </el-table-column>
        <el-table-column prop="service_type" label="服务方式" min-width="120" />
        <el-table-column prop="open_time" label="营业时间" min-width="150" />
        <el-table-column prop="contact_phone" label="联系电话" min-width="160" />
        <el-table-column label="营业状态" min-width="120">
          <template #default="{ row }">
            <el-switch
              :model-value="normalizeStatus(row.status)"
              inline-prompt
              active-text="营业"
              inactive-text="停用"
              @change="toggleStatus(row, $event)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="address" label="地址" min-width="240" show-overflow-tooltip />
        <el-table-column label="操作" fixed="right" min-width="200">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeCanteen(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="currentId ? '编辑档口' : '新增档口'" width="620px" @closed="handleClosed">
      <el-form ref="formRef" label-width="100px" :model="form" :rules="rules">
        <el-form-item label="档口名称" prop="canteen_name">
          <el-input v-model="form.canteen_name" />
        </el-form-item>
        <el-form-item label="楼栋" prop="building">
          <el-input v-model="form.building" />
        </el-form-item>
        <el-form-item label="楼层" prop="floor">
          <el-input v-model="form.floor" />
        </el-form-item>
        <el-form-item label="窗口号" prop="window_no">
          <el-input v-model="form.window_no" />
        </el-form-item>
        <el-form-item label="服务方式" prop="service_type">
          <el-select v-model="form.service_type" style="width: 100%">
            <el-option label="自取" value="pickup" />
            <el-option label="配送" value="delivery" />
          </el-select>
        </el-form-item>
        <el-form-item label="营业时间" prop="open_time">
          <el-input v-model="form.open_time" placeholder="例如 08:00-20:00" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="form.contact_phone" />
        </el-form-item>
        <el-form-item label="详细地址" prop="address">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="form.latitude" :precision="6" style="width: 100%" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="form.longitude" :precision="6" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { canteenApi } from '@/api/modules/canteens'
import { normalizeListPayload } from '@/utils/formatters'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const currentId = ref(null)
const formRef = ref(null)
const list = ref([])
const query = reactive({ keyword: '', status: undefined })
const form = reactive({
  canteen_name: '',
  building: '',
  floor: '',
  window_no: '',
  service_type: 'pickup',
  open_time: '',
  contact_phone: '',
  latitude: null,
  longitude: null,
  address: '',
  status: 1
})

const rules = {
  canteen_name: [{ required: true, message: '请输入档口名称', trigger: 'blur' }],
  building: [{ required: true, message: '请输入楼栋', trigger: 'blur' }],
  floor: [{ required: true, message: '请输入楼层', trigger: 'blur' }],
  window_no: [{ required: true, message: '请输入窗口号', trigger: 'blur' }],
  service_type: [{ required: true, message: '请选择服务方式', trigger: 'change' }],
  open_time: [{ required: true, message: '请输入营业时间', trigger: 'blur' }],
  contact_phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '请输入正确的 11 位手机号', trigger: 'blur' }
  ],
  address: [{ required: true, message: '请输入详细地址', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const normalizeStatus = (value) => Number(value) === 1 || value === true || value === 'enabled'

const loadData = async () => {
  loading.value = true
  try {
    const result = await canteenApi.getList({ ...query })
    list.value = normalizeListPayload(result).items
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载档口列表失败')
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

const resetFilters = () => {
  query.page = 1
  query.page_size = 10
  query.keyword = ''
  query.status = undefined
  loadData()
}

const resetForm = () => {
  currentId.value = null
  Object.assign(form, {
    canteen_name: '',
    building: '',
    floor: '',
    window_no: '',
    service_type: 'pickup',
    open_time: '',
    contact_phone: '',
    latitude: null,
    longitude: null,
    address: '',
    status: 1
  })
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

const openEdit = (row) => {
  currentId.value = row.canteen_id
  Object.assign(form, {
    canteen_name: row.canteen_name || '',
    building: row.building || '',
    floor: row.floor || '',
    window_no: row.window_no || '',
    service_type: row.service_type || 'pickup',
    open_time: row.open_time || '',
    contact_phone: row.contact_phone || '',
    latitude: row.latitude ?? null,
    longitude: row.longitude ?? null,
    address: row.address || '',
    status: Number(row.status ?? 1)
  })
  dialogVisible.value = true
}

const submitForm = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请先完善档口信息后再保存')
    return
  }

  submitting.value = true
  try {
    const payload = { ...form }
    if (currentId.value) {
      await canteenApi.update(currentId.value, payload)
      ElMessage.success('档口已更新')
    } else {
      await canteenApi.create(payload)
      ElMessage.success('档口已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存档口失败')
  } finally {
    submitting.value = false
  }
}

const toggleStatus = async (row, enabled) => {
  try {
    await canteenApi.updateStatus(row.canteen_id, enabled ? 1 : 0)
    ElMessage.success(enabled ? '档口已启用' : '档口已停用')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '更新档口状态失败')
    await loadData()
  }
}

const removeCanteen = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除档口「${row.canteen_name}」吗？`, '删除档口', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除档口')
    return
  }

  try {
    await canteenApi.remove(row.canteen_id)
    ElMessage.success('档口已删除')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除档口失败')
  }
}

onMounted(loadData)
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

.toolbar-actions {
  display: flex;
  gap: 12px;
}
</style>
