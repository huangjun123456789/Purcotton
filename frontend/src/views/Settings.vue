<template>
  <div class="settings-container">
    <el-row :gutter="20">
      <!-- 个人资料 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>个人资料</span>
            </div>
          </template>
          
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="80px"
          >
            <el-form-item label="用户名">
              <el-input :value="user?.username" disabled />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag :type="user?.role === 'admin' ? 'danger' : 'info'">
                {{ user?.role === 'admin' ? '管理员' : '普通用户' }}
              </el-tag>
            </el-form-item>
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="profileForm.nickname" placeholder="请输入昵称" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="profileLoading" @click="handleUpdateProfile">
                保存资料
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 修改密码 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Lock /></el-icon>
              <span>修改密码</span>
            </div>
          </template>
          
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="80px"
          >
            <el-form-item label="当前密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 账户信息 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <el-icon><InfoFilled /></el-icon>
          <span>账户信息</span>
        </div>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="账户ID">{{ user?.id }}</el-descriptions-item>
        <el-descriptions-item label="账户状态">
          <el-tag :type="user?.is_active ? 'success' : 'danger'">
            {{ user?.is_active ? '正常' : '已禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最后登录">
          {{ user?.last_login ? formatDate(user.last_login) : '从未登录' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ user?.created_at ? formatDate(user.created_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ user?.updated_at ? formatDate(user.updated_at) : '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, InfoFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const userStore = useUserStore()
const user = computed(() => userStore.user)

// 个人资料表单
const profileFormRef = ref<FormInstance>()
const profileLoading = ref(false)
const profileForm = reactive({
  nickname: '',
  email: '',
  phone: ''
})

const profileRules: FormRules = {
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号', trigger: 'blur' }
  ]
}

// 修改密码表单
const passwordFormRef = ref<FormInstance>()
const passwordLoading = ref(false)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度至少为 6 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 初始化表单数据
const initProfileForm = () => {
  if (user.value) {
    profileForm.nickname = user.value.nickname || ''
    profileForm.email = user.value.email || ''
    profileForm.phone = user.value.phone || ''
  }
}

// 监听用户信息变化
watch(user, () => {
  initProfileForm()
}, { immediate: true })

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 更新个人资料
const handleUpdateProfile = async () => {
  if (!profileFormRef.value) return
  
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    profileLoading.value = true
    try {
      await userStore.updateProfile({
        nickname: profileForm.nickname || undefined,
        email: profileForm.email || undefined,
        phone: profileForm.phone || undefined
      })
      ElMessage.success('资料更新成功')
    } catch (error: any) {
      const message = error.response?.data?.detail || '更新失败'
      ElMessage.error(message)
    } finally {
      profileLoading.value = false
    }
  })
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    passwordLoading.value = true
    try {
      await userStore.changePassword(
        passwordForm.old_password,
        passwordForm.new_password
      )
      ElMessage.success('密码修改成功')
      // 清空表单
      passwordForm.old_password = ''
      passwordForm.new_password = ''
      passwordForm.confirm_password = ''
      passwordFormRef.value?.resetFields()
    } catch (error: any) {
      const message = error.response?.data?.detail || '密码修改失败'
      ElMessage.error(message)
    } finally {
      passwordLoading.value = false
    }
  })
}

onMounted(() => {
  // 如果用户信息不完整，重新获取
  if (!user.value?.id) {
    userStore.fetchCurrentUser()
  }
})
</script>

<style lang="scss" scoped>
.settings-container {
  padding: 20px;
  height: 100%;
  overflow: auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .el-icon {
    font-size: 18px;
  }
}

:deep(.el-form) {
  max-width: 400px;
}
</style>
