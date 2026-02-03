<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <el-icon :size="48" color="#409eff"><DataBoard /></el-icon>
        <h1>WMS 仓库热力图系统</h1>
        <p>Warehouse Heatmap Management System</p>
      </div>
      
      <!-- 登录模式选择 -->
      <div class="login-mode-tabs">
        <div 
          class="mode-tab" 
          :class="{ active: loginMode === 'user' }"
          @click="loginMode = 'user'"
        >
          <el-icon><View /></el-icon>
          <span>普通用户</span>
        </div>
        <div 
          class="mode-tab" 
          :class="{ active: loginMode === 'admin' }"
          @click="loginMode = 'admin'"
        >
          <el-icon><Setting /></el-icon>
          <span>管理员</span>
        </div>
      </div>
      
      <!-- 普通用户模式 -->
      <div v-if="loginMode === 'user'" class="user-mode">
        <div class="user-mode-desc">
          <el-icon :size="64" color="#67c23a"><UserFilled /></el-icon>
          <p class="desc-title">普通用户访问</p>
          <p class="desc-text">无需登录，可查看库位分布、热力图和导出报告</p>
        </div>
        <el-button
          type="success"
          size="large"
          class="login-button"
          @click="handleGuestLogin"
        >
          <el-icon><Right /></el-icon>
          立即进入系统
        </el-button>
      </div>
      
      <!-- 管理员登录模式 -->
      <div v-else class="admin-mode">
        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="rules"
          class="login-form"
          @keyup.enter="handleAdminLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入管理员账号"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-button"
              :loading="loading"
              @click="handleAdminLogin"
            >
              {{ loading ? '登录中...' : '管理员登录' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, DataBoard, View, Setting, UserFilled, Right } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const loginMode = ref<'user' | 'admin'>('user')

const loginForm = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入管理员账号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 普通用户直接进入（访客模式）
const handleGuestLogin = () => {
  userStore.loginAsGuest()
  ElMessage.success('欢迎使用系统')
  const redirect = route.query.redirect as string
  router.push(redirect || '/')
}

// 管理员登录
const handleAdminLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await userStore.login({
        username: loginForm.username,
        password: loginForm.password
      })
      
      ElMessage.success('登录成功')
      
      // 跳转到之前访问的页面或首页
      const redirect = route.query.redirect as string
      router.push(redirect || '/')
    } catch (error: any) {
      const message = error.response?.data?.detail || '登录失败，请检查用户名和密码'
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  
  h1 {
    margin: 16px 0 8px;
    font-size: 24px;
    color: #303133;
  }
  
  p {
    margin: 0;
    font-size: 14px;
    color: #909399;
  }
}

.login-mode-tabs {
  display: flex;
  margin-bottom: 30px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
  
  .mode-tab {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 14px 0;
    cursor: pointer;
    transition: all 0.3s;
    color: #606266;
    background: #f5f7fa;
    
    &:hover {
      color: #409eff;
    }
    
    &.active {
      background: #409eff;
      color: #fff;
    }
    
    .el-icon {
      font-size: 18px;
    }
    
    span {
      font-size: 15px;
      font-weight: 500;
    }
  }
}

.user-mode {
  .user-mode-desc {
    text-align: center;
    padding: 20px 0 30px;
    
    .desc-title {
      margin: 16px 0 8px;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
    
    .desc-text {
      margin: 0;
      font-size: 14px;
      color: #909399;
      line-height: 1.6;
    }
  }
}

.admin-mode {
  .login-form {
    .el-form-item {
      margin-bottom: 24px;
    }
    
    .el-input {
      :deep(.el-input__wrapper) {
        padding: 4px 12px;
      }
    }
  }
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
}
</style>
