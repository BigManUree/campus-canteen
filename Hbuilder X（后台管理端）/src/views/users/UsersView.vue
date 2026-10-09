<template>
  <div class="page-shell page-stack">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>用户管理</h3>
            <p>严格按文档接口维护用户资料、角色与状态。</p>
          </div>
          <div class="toolbar-actions">
            <el-input v-model="query.keyword" clearable placeholder="用户名 / 昵称 / 手机号 / 学号" style="width: 280px" @clear="handleFilterChange" @keyup.enter="handleSearch" />
            <el-select v-model="query.role" clearable placeholder="角色" style="width: 160px" @change="handleFilterChange">
              <el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="query.status" clearable placeholder="状态" style="width: 140px" @change="handleFilterChange">
              <el-option label="启用" :value="1" />
              <el-option label="禁用" :value="0" />
            </el-select>
            <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" row-key="user_id">
        <el-table-column prop="user_id" label="用户 ID" min-width="90" />
        <el-table-column label="用户信息" min-width="260">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="avatar">{{ (row.nickname || row.username || 'U').slice(0, 1) }}</div>
              <div>
                <strong>{{ row.nickname || row.username || '-' }}</strong>
                <p>{{ row.username || '-' }}</p>
                <span>{{ row.phone || row.email || '未填写联系方式' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="130">
          <template #default="{ row }">
            <el-tag>{{ roleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="110">
          <template #default="{ row }">
            <el-switch
              :model-value="normalizeStatus(row.status)"
              inline-prompt
              active-text="启用"
              inactive-text="禁用"
              @change="toggleStatus(row, $event)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="student_no" label="学号" min-width="120" />
        <el-table-column label="订单数" min-width="100">
          <template #default="{ row }">{{ row.order_count ?? 0 }}</template>
        </el-table-column>
        <el-table-column prop="department" label="院系" min-width="150" />
        <el-table-column label="注册时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="240">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-dropdown>
                <el-button size="small" type="primary" plain>
                  修改角色
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item v-for="item in roleOptions" :key="item.value" @click="changeRole(row, item.value)">{{ item.label }}</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button size="small" type="danger" plain :disabled="isSelf(row)" @click="removeUser(row)">删除</el-button>
            </el-space>
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

    <el-drawer v-model="drawerVisible" title="编辑用户" size="520px" @closed="handleDrawerClosed">
      <el-form ref="formRef" label-width="100px" :model="form" :rules="rules">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="form.student_no" disabled />
        </el-form-item>
        <el-form-item label="院系">
          <el-input v-model="form.department" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-space>
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitEdit">保存</el-button>
        </el-space>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api/modules/users'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime, normalizeListPayload } from '@/utils/formatters'

const authStore = useAuthStore()
const loading = ref(false)
const submitting = ref(false)
const drawerVisible = ref(false)
const formRef = ref(null)
const list = ref([])
const currentId = ref(null)
const pagination = reactive({ total: 0 })
const query = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  role: undefined,
  status: undefined
})
const form = reactive({
  username: '',
  nickname: '',
  phone: '',
  email: '',
  student_no: '',
  department: '',
  role: 'student',
  status: 1
})

const rules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  phone: [{ pattern: /^$|^1\d{10}$/, message: '请输入正确的 11 位手机号', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }]
}

const roleOptions = [
  { label: '学生', value: 'student' },
  { label: '商家管理员', value: 'merchant' },
  { label: '管理员', value: 'admin' },
  { label: '系统管理员', value: 'sys_admin' },
  { label: '档口管理员', value: 'canteen_admin' },
  { label: '普通用户', value: 'user' }
]

const roleText = (role) => roleOptions.find((item) => item.value === role)?.label || role || '未知角色'
const normalizeStatus = (value) => Number(value) === 1 || value === true || value === 'enabled'

const loadData = async () => {
  loading.value = true
  try {
    const result = await userApi.getList({ ...query })
    const normalized = normalizeListPayload(result)
    list.value = normalized.items
    pagination.total = normalized.total
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
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

const handleSearch = () => {
  query.page = 1
  loadData()
}

const resetFilters = () => {
  query.page = 1
  query.page_size = 10
  query.keyword = ''
  query.role = undefined
  query.status = undefined
  loadData()
}

const resetForm = () => {
  currentId.value = null
  Object.assign(form, {
    username: '',
    nickname: '',
    phone: '',
    email: '',
    student_no: '',
    department: '',
    role: 'student',
    status: 1
  })
}

const openEdit = async (row) => {
  currentId.value = row.user_id
  try {
    const detailResponse = await userApi.getDetail(row.user_id)
    const detail = detailResponse?.data || detailResponse
    Object.assign(form, {
      username: detail.username || '',
      nickname: detail.nickname || '',
      phone: detail.phone || '',
      email: detail.email || '',
      student_no: detail.student_no || '',
      department: detail.department || '',
      role: detail.role || 'student',
      status: Number(detail.status ?? 1)
    })
  } catch (_error) {
    Object.assign(form, {
      username: row.username || '',
      nickname: row.nickname || '',
      phone: row.phone || '',
      email: row.email || '',
      student_no: row.student_no || '',
      department: row.department || '',
      role: row.role || 'student',
      status: Number(row.status ?? 1)
    })
    ElMessage.warning('用户详情加载失败，已使用列表数据填充')
  }
  drawerVisible.value = true
  formRef.value?.clearValidate()
}

const submitEdit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请先完善用户信息后再保存')
    return
  }

  submitting.value = true
  try {
    await userApi.update(currentId.value, {
      nickname: form.nickname,
      phone: form.phone,
      email: form.email,
      role: form.role,
      status: form.status
    })
    ElMessage.success('用户资料已更新')
    drawerVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存用户资料失败')
  } finally {
    submitting.value = false
  }
}

const handleDrawerClosed = () => {
  formRef.value?.resetFields()
  formRef.value?.clearValidate()
  resetForm()
}

const isSelf = (row) => Number(row.user_id) === Number(authStore.user?.user_id)

const changeRole = async (row, role) => {
  if (row.role === role) {
    ElMessage.info('该用户已是当前角色')
    return
  }
  try {
    await userApi.updateRole(row.user_id, { role })
    ElMessage.success('角色已更新')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '更新角色失败')
  }
}

const toggleStatus = async (row, enabled) => {
  try {
    await userApi.updateStatus(row.user_id, { status: enabled ? 1 : 0 })
    ElMessage.success(enabled ? '用户已启用' : '用户已禁用')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '更新用户状态失败')
    await loadData()
  }
}

const removeUser = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除用户「${row.nickname || row.username || row.user_id}」吗？`, '删除用户', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除用户')
    return
  }

  try {
    await userApi.remove(row.user_id)
    ElMessage.success('用户已删除')
    if (list.value.length === 1 && query.page > 1) {
      query.page -= 1
    }
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除用户失败')
  }
}

onMounted(loadData)
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

.toolbar-actions,
.pagination-wrap {
  display: flex;
  gap: 12px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;

  .avatar,
  .avatar-image {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    overflow: hidden;
    flex-shrink: 0;
  }

  .avatar {
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #6ea8fe, #9b7bff);
    color: #fff;
    font-weight: 700;
  }

  p,
  span {
    margin: 4px 0 0;
    color: #90a0c0;
    font-size: 13px;
  }
}

.pagination-wrap {
  justify-content: flex-end;
  margin-top: 22px;
}
</style>
