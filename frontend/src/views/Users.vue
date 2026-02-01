<template>
  <div class="users-container">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            添加用户
          </el-button>
        </div>
      </template>
      
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名/昵称"
          clearable
          style="width: 200px"
          @clear="loadUsers"
          @keyup.enter="loadUsers"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="filterRole" placeholder="角色筛选" clearable style="width: 120px" @change="loadUsers">
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="user" />
        </el-select>
        <el-select v-model="filterActive" placeholder="状态筛选" clearable style="width: 120px" @change="loadUsers">
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
        <el-button @click="loadUsers">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      
      <!-- 用户列表 -->
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="nickname" label="昵称" width="120">
          <template #default="{ row }">
            {{ row.nickname || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" width="180">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="130">
          <template #default="{ row }">
            {{ row.phone || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="160">
          <template #default="{ row }">
            {{ row.last_login ? formatDate(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="warning" link @click="handleResetPassword(row)">
              <el-icon><Key /></el-icon>
              重置密码
            </el-button>
            <el-button 
              :type="row.is_active ? 'danger' : 'success'" 
              link 
              @click="handleToggleActive(row)"
              :disabled="row.id === currentUser?.id"
            >
              <el-icon><component :is="row.is_active ? 'Lock' : 'Unlock'" /></el-icon>
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              type="danger" 
              link 
              @click="handleDelete(row)"
              :disabled="row.id === currentUser?.id"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadUsers"
          @current-change="loadUsers"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '添加用户'"
      width="500px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="userForm" :rules="formRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="isEdit" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="userForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态" prop="is_active">
          <el-switch v-model="userForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPwdDialogVisible" title="重置密码" width="400px">
      <el-form ref="resetPwdFormRef" :model="resetPwdForm" :rules="resetPwdRules" label-width="80px">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetPwdForm.new_password" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="resetPwdForm.confirm_password" type="password" placeholder="请再次输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitResetPassword">
          确定重置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, Key, Delete, Lock, Unlock } from '@element-plus/icons-vue'
import { userApi } from '@/api'
import { useUserStore } from '@/stores/user'
import type { User, UserRole } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

const userStore = useUserStore()
const currentUser = computed(() => userStore.user)

// 列表状态
const loading = ref(false)
const users = ref<User[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')
const filterRole = ref<string>('')
const filterActive = ref<boolean | ''>('')

// 对话框状态
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingUserId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

// 用户表单
const userForm = reactive({
  username: '',
  password: '',
  nickname: '',
  email: '',
  phone: '',
  role: 'user' as UserRole,
  is_active: true
})

// 表单验证规则
const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度为 2-50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度至少为 6 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 重置密码
const resetPwdDialogVisible = ref(false)
const resetPwdUserId = ref<number | null>(null)
const resetPwdFormRef = ref<FormInstance>()
const resetPwdForm = reactive({
  new_password: '',
  confirm_password: ''
})

const resetPwdRules: FormRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度至少为 6 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== resetPwdForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
}

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterRole.value) params.role = filterRole.value
    if (filterActive.value !== '') params.is_active = filterActive.value
    
    const [usersData, countData] = await Promise.all([
      userApi.getUsers(params),
      userApi.getUsersCount({
        role: filterRole.value || undefined,
        is_active: filterActive.value !== '' ? filterActive.value : undefined,
        keyword: searchKeyword.value || undefined
      })
    ])
    
    users.value = usersData
    total.value = countData.count
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

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

// 打开创建对话框
const openCreateDialog = () => {
  isEdit.value = false
  editingUserId.value = null
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (user: User) => {
  isEdit.value = true
  editingUserId.value = user.id
  userForm.username = user.username
  userForm.nickname = user.nickname || ''
  userForm.email = user.email || ''
  userForm.phone = user.phone || ''
  userForm.role = user.role
  userForm.is_active = user.is_active
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  userForm.username = ''
  userForm.password = ''
  userForm.nickname = ''
  userForm.email = ''
  userForm.phone = ''
  userForm.role = 'user'
  userForm.is_active = true
  formRef.value?.resetFields()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isEdit.value && editingUserId.value) {
        await userApi.updateUser(editingUserId.value, {
          nickname: userForm.nickname || undefined,
          email: userForm.email || undefined,
          phone: userForm.phone || undefined,
          role: userForm.role,
          is_active: userForm.is_active
        })
        ElMessage.success('用户更新成功')
      } else {
        await userApi.createUser({
          username: userForm.username,
          password: userForm.password,
          nickname: userForm.nickname || undefined,
          email: userForm.email || undefined,
          phone: userForm.phone || undefined,
          role: userForm.role
        })
        ElMessage.success('用户创建成功')
      }
      dialogVisible.value = false
      loadUsers()
    } catch (error: any) {
      const message = error.response?.data?.detail || '操作失败'
      ElMessage.error(message)
    } finally {
      submitting.value = false
    }
  })
}

// 重置密码
const handleResetPassword = (user: User) => {
  resetPwdUserId.value = user.id
  resetPwdForm.new_password = ''
  resetPwdForm.confirm_password = ''
  resetPwdDialogVisible.value = true
}

const submitResetPassword = async () => {
  if (!resetPwdFormRef.value || !resetPwdUserId.value) return
  
  await resetPwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      await userApi.resetPassword(resetPwdUserId.value!, {
        new_password: resetPwdForm.new_password
      })
      ElMessage.success('密码重置成功')
      resetPwdDialogVisible.value = false
    } catch (error: any) {
      const message = error.response?.data?.detail || '重置密码失败'
      ElMessage.error(message)
    } finally {
      submitting.value = false
    }
  })
}

// 切换用户状态
const handleToggleActive = async (user: User) => {
  const action = user.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${user.username}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await userApi.toggleUserActive(user.id)
    ElMessage.success(`${action}成功`)
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      const message = error.response?.data?.detail || `${action}失败`
      ElMessage.error(message)
    }
  }
}

// 删除用户
const handleDelete = async (user: User) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${user.username}" 吗？此操作不可恢复！`, '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    await userApi.deleteUser(user.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      const message = error.response?.data?.detail || '删除失败'
      ElMessage.error(message)
    }
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style lang="scss" scoped>
.users-container {
  padding: 20px;
  height: 100%;
  overflow: auto;
}

.page-card {
  height: 100%;
  
  :deep(.el-card__body) {
    height: calc(100% - 60px);
    display: flex;
    flex-direction: column;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
