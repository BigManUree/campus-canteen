<template>
  <div class="auth-page">
    <div class="auth-page__backdrop"></div>
    <el-card class="auth-card" shadow="never">
      <div class="auth-brand">
        <div class="auth-brand__mark">CC</div>
        <div>
          <h1>校园食堂管理后台</h1>
          <p>Vue 3 · Element Plus · API First</p>
        </div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入管理员账号" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入登录密码" :prefix-icon="Lock" />
        </el-form-item>
        <el-button class="submit-btn" type="primary" :loading="submitting" @click="handleSubmit">登录管理端</el-button>
      </el-form>

      <div class="auth-footer">
        <span>默认接口地址：{{ baseUrl }}</span>
        <span>仅支持管理员 / 系统管理员 / 商家管理员 / 档口管理员登录</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { BASE_URL } from '@/utils/constants'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const submitting = ref(false)
const baseUrl = BASE_URL || '/api-proxy'

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    ElMessage.warning('请输入账号和密码后再登录')
    return
  }

  submitting.value = true
  try {
    await authStore.login(form)
    ElMessage.success('登录成功，欢迎进入管理后台')
    router.replace('/dashboard')
  } catch (error) {
    if (error?.message === '当前账号无管理端访问权限') {
      ElMessage.error(error.message)
      return
    }
    ElMessage.error(error?.userMessage || error?.message || '登录失败，请检查账号密码后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.auth-page {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 100vh;
  overflow: hidden;
}

.auth-page__backdrop {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 18% 18%, rgba(36, 201, 154, 0.3), transparent 22%),
    radial-gradient(circle at 82% 16%, rgba(255, 184, 77, 0.2), transparent 18%),
    radial-gradient(circle at 60% 84%, rgba(110, 168, 254, 0.18), transparent 20%);
  filter: blur(18px);
}

.auth-card {
  position: relative;
  width: 480px;
  padding: 12px;
  border-radius: 28px;
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;

  h1 {
    margin: 0;
    font-size: 28px;
  }

  p {
    margin: 10px 0 0;
    color: #93a0c2;
    letter-spacing: 0.08em;
  }
}

.auth-brand__mark {
  display: grid;
  place-items: center;
  width: 62px;
  height: 62px;
  border-radius: 20px;
  background: linear-gradient(135deg, #24c99a, #6ea8fe);
  color: #04111d;
  font-size: 24px;
  font-weight: 900;
}

.submit-btn {
  width: 100%;
  height: 50px;
  margin-top: 10px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, #24c99a, #6ea8fe);
}

.auth-footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 22px;
  color: #8d98b5;
  font-size: 13px;
}
</style>
