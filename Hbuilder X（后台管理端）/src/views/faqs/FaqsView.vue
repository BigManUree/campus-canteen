<template>
  <div class="page-shell">
    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="toolbar">
          <div>
            <h3>常见问题</h3>
            <p>按文档真实字段维护常见问题分类、排序、状态与问答内容。</p>
          </div>
          <el-button type="primary" @click="openCreate">新增常见问题</el-button>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" row-key="faq_id">
        <el-table-column prop="faq_id" label="FAQ ID" min-width="100" />
        <el-table-column prop="category" label="分类" min-width="120" />
        <el-table-column prop="question" label="问题" min-width="280" show-overflow-tooltip />
        <el-table-column prop="answer" label="回答" min-width="360" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" min-width="100" />
        <el-table-column label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="Number(row.status) === 1 ? 'success' : 'info'">{{ Number(row.status) === 1 ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.update_time || row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" min-width="180">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeFaq(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="currentId ? '编辑常见问题' : '新增常见问题'" width="640px" @closed="handleClosed">
      <el-form ref="formRef" label-width="90px" :model="form" :rules="rules">
        <el-form-item label="分类" prop="category">
          <el-input v-model="form.category" />
        </el-form-item>
        <el-form-item label="问题" prop="question">
          <el-input v-model="form.question" />
        </el-form-item>
        <el-form-item label="回答" prop="answer">
          <el-input v-model="form.answer" type="textarea" :rows="8" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">停用</el-radio>
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
import { faqApi } from '@/api/modules/faqs'
import { formatDateTime, normalizeListPayload } from '@/utils/formatters'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const currentId = ref(null)
const formRef = ref(null)
const list = ref([])
const form = reactive({ category: '', question: '', answer: '', sort_order: 0, status: 1 })
const rules = {
  category: [{ required: true, message: '请输入问题分类', trigger: 'blur' }],
  question: [{ required: true, message: '请输入问题内容', trigger: 'blur' }],
  answer: [{ required: true, message: '请输入回答内容', trigger: 'blur' }],
  sort_order: [{ required: true, message: '请输入排序值', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const result = await faqApi.getList({ page: 1, page_size: 100 })
    list.value = normalizeListPayload(result).items
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载常见问题列表失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  currentId.value = null
  Object.assign(form, { category: '', question: '', answer: '', sort_order: 0, status: 1 })
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row) => {
  currentId.value = row.faq_id
  Object.assign(form, {
    category: row.category || '',
    question: row.question || '',
    answer: row.answer || '',
    sort_order: Number(row.sort_order || 0),
    status: Number(row.status ?? 1)
  })
  dialogVisible.value = true
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
    ElMessage.warning('请先完善常见问题内容后再保存')
    return
  }
  submitting.value = true
  try {
    if (currentId.value) {
      await faqApi.update(currentId.value, { ...form })
      ElMessage.success('常见问题已更新')
    } else {
      await faqApi.create({ ...form })
      ElMessage.success('常见问题已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存常见问题失败')
  } finally {
    submitting.value = false
  }
}

const removeFaq = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除常见问题「${row.question || row.faq_id}」吗？`, '删除常见问题', { type: 'warning' })
  } catch {
    ElMessage.info('已取消删除常见问题')
    return
  }
  try {
    await faqApi.remove(row.faq_id)
    ElMessage.success('常见问题已删除')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除常见问题失败')
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
</style>
