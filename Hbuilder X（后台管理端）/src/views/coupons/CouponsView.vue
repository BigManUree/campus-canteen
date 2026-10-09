<template>
  <div class="page-shell">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>优惠券管理</h3>
            <p>创建优惠券并维护有效期与启用状态。</p>
          </div>
          <div class="toolbar-actions">
            <el-select v-model="query.status" clearable placeholder="状态筛选" style="width: 160px" @change="handleSearch">
              <el-option label="未启用" :value="0" />
              <el-option label="启用" :value="1" />
            </el-select>
            <el-button @click="openCreate">新增优惠券</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" row-key="coupon_id">
        <el-table-column prop="coupon_id" label="优惠券 ID" min-width="110" />
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column label="优惠类型" min-width="120">
          <template #default="{ row }">{{ row.coupon_type || 'cash' }}</template>
        </el-table-column>
        <el-table-column label="金额/门槛" min-width="180">
          <template #default="{ row }">¥{{ currency(row.discount_value || 0) }} / 满 ¥{{ currency(row.min_amount || 0) }}</template>
        </el-table-column>
        <el-table-column label="有效期" min-width="240">
          <template #default="{ row }">{{ formatDateTime(row.start_time) }} 至 {{ formatDateTime(row.end_time) }}</template>
        </el-table-column>
        <el-table-column label="状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="Number(row.status) === 1 ? 'success' : 'info'">{{ Number(row.status) === 1 ? '启用' : '未启用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="200">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" @click="toggleStatus(row)">{{ Number(row.status) === 1 ? '停用' : '启用' }}</el-button>
              <el-button size="small" type="danger" plain @click="removeCoupon(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="currentId ? '编辑优惠券' : '新增优惠券'" width="620px" @closed="handleClosed">
      <el-form ref="formRef" label-width="108px" :model="form" :rules="rules">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="优惠描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="优惠类型" prop="coupon_type">
          <el-select v-model="form.coupon_type" style="width: 100%">
            <el-option label="满减券" value="cash" />
            <el-option label="折扣券" value="discount" />
          </el-select>
        </el-form-item>
        <el-form-item label="优惠金额" prop="discount_value">
          <el-input-number v-model="form.discount_value" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="使用门槛" prop="min_amount">
          <el-input-number v-model="form.min_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="总库存" prop="total_count">
          <el-input-number v-model="form.total_count" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">未启用</el-radio>
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
import { couponApi } from '@/api/modules/coupons'
import { currency, formatDateTime, normalizeListPayload, toNumber } from '@/utils/formatters'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const currentId = ref(null)
const formRef = ref(null)
const list = ref([])
const query = reactive({ status: undefined })
const form = reactive({
  name: '',
  description: '',
  coupon_type: 'cash',
  discount_value: 0,
  min_amount: 0,
  max_discount: null,
  total_count: 1,
  start_time: '',
  end_time: '',
  status: 1
})

const validateCouponAmount = (_rule, value, callback) => {
  const amount = toNumber(value)
  const threshold = toNumber(form.min_amount)
  if (amount <= 0) {
    callback(new Error('优惠金额必须大于 0'))
    return
  }
  if (threshold < 0) {
    callback(new Error('使用门槛不能小于 0'))
    return
  }
  if (amount > 0 && threshold > 0 && threshold < amount) {
    callback(new Error('使用门槛不能小于优惠金额'))
    return
  }
  callback()
}

const validateCouponEndTime = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请选择结束时间'))
    return
  }
  if (!form.start_time) {
    callback()
    return
  }
  if (new Date(value).getTime() <= new Date(form.start_time).getTime()) {
    callback(new Error('结束时间必须晚于开始时间'))
    return
  }
  callback()
}

const rules = {
  name: [{ required: true, message: '请输入优惠券名称', trigger: 'blur' }],
  coupon_type: [{ required: true, message: '请选择优惠类型', trigger: 'change' }],
  discount_value: [
    { required: true, message: '请输入优惠金额', trigger: 'change' },
    { validator: validateCouponAmount, trigger: 'change' }
  ],
  min_amount: [
    { required: true, message: '请输入使用门槛', trigger: 'change' },
    { validator: validateCouponAmount, trigger: 'change' }
  ],
  total_count: [{ required: true, message: '请输入总库存', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    { validator: validateCouponEndTime, trigger: 'change' }
  ],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const result = await couponApi.getList({ status: query.status })
    list.value = normalizeListPayload(result).items
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载优惠券列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  loadData()
}

const resetForm = () => {
  currentId.value = null
  Object.assign(form, {
    name: '',
    description: '',
    coupon_type: 'cash',
    discount_value: 0,
    min_amount: 0,
    max_discount: null,
    start_time: '',
    end_time: '',
    status: 1
  })
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

const openEdit = (row) => {
  currentId.value = row.coupon_id
  Object.assign(form, {
    name: row.name || '',
    description: row.description || '',
    coupon_type: row.coupon_type || 'cash',
    discount_value: Number(row.discount_value || 0),
    min_amount: Number(row.min_amount || 0),
    max_discount: row.max_discount ?? null,
    total_count: Number(row.total_count || 1),
    start_time: row.start_time || '',
    end_time: row.end_time || '',
    status: Number(row.status ?? 1)
  })
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

const handleClosed = () => {
  formRef.value?.resetFields()
  formRef.value?.clearValidate()
  resetForm()
}

const submitForm = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请先完整填写表单后再保存')
    return
  }

  submitting.value = true
  try {
    const payload = {
      name: form.name,
      description: form.description,
      coupon_type: form.coupon_type,
      discount_value: form.discount_value,
      min_amount: form.min_amount,
      max_discount: form.max_discount,
      start_time: form.start_time,
      end_time: form.end_time,
      total_count: form.total_count
    }

    if (currentId.value) {
      await couponApi.update(currentId.value, payload)
      ElMessage.success('优惠券已更新')
    } else {
      await couponApi.create(payload)
      ElMessage.success('优惠券已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存优惠券失败')
  } finally {
    submitting.value = false
  }
}

const toggleStatus = async (row) => {
  const nextStatus = Number(row.status) === 1 ? 0 : 1
  try {
    await couponApi.updateStatus(row.coupon_id, nextStatus)
    ElMessage.success(nextStatus === 1 ? '优惠券已启用' : '优惠券已停用')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '更新优惠券状态失败')
  }
}

const removeCoupon = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除优惠券「${row.name}」吗？`, '删除优惠券', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除优惠券')
    return
  }

  try {
    const result = await couponApi.remove(row.coupon_id)
    ElMessage.success(result?.message || '优惠券已删除')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除优惠券失败')
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.toolbar,
.toolbar-actions {
  display: flex;
  gap: 18px;
}

.toolbar {
  align-items: center;
  justify-content: space-between;

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
  align-items: center;
}
</style>
