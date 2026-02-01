import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, UserProfileUpdate } from '@/types'
import { authApi } from '@/api'

// Token 存储 key
const TOKEN_KEY = 'access_token'
const USER_KEY = 'user_info'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const username = computed(() => user.value?.username || '')
  const displayName = computed(() => user.value?.nickname || user.value?.username || '用户')
  const userRole = computed(() => user.value?.role || 'user')

  // 登录
  const login = async (loginData: LoginRequest): Promise<boolean> => {
    loading.value = true
    try {
      const response = await authApi.login(loginData)
      
      // 保存 token 和用户信息
      token.value = response.access_token
      user.value = response.user
      
      localStorage.setItem(TOKEN_KEY, response.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(response.user))
      
      return true
    } catch (error: any) {
      console.error('登录失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 退出登录
  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('退出登录失败:', error)
    } finally {
      // 无论请求是否成功，都清除本地状态
      token.value = null
      user.value = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  }

  // 获取当前用户信息
  const fetchCurrentUser = async (): Promise<User | null> => {
    if (!token.value) return null
    
    loading.value = true
    try {
      const userData = await authApi.getCurrentUser()
      user.value = userData
      localStorage.setItem(USER_KEY, JSON.stringify(userData))
      return userData
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取失败，可能是 token 失效
      logout()
      return null
    } finally {
      loading.value = false
    }
  }

  // 更新个人资料
  const updateProfile = async (data: UserProfileUpdate): Promise<User> => {
    loading.value = true
    try {
      const updatedUser = await authApi.updateProfile(data)
      user.value = updatedUser
      localStorage.setItem(USER_KEY, JSON.stringify(updatedUser))
      return updatedUser
    } finally {
      loading.value = false
    }
  }

  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string): Promise<void> => {
    await authApi.changePassword({
      old_password: oldPassword,
      new_password: newPassword
    })
  }

  // 检查是否有指定权限
  const hasPermission = (requiredRole: 'admin' | 'user'): boolean => {
    if (!user.value) return false
    if (requiredRole === 'user') return true // 所有已登录用户都有 user 权限
    return user.value.role === 'admin'
  }

  // 初始化 - 验证 token 有效性
  const initializeAuth = async () => {
    if (token.value) {
      await fetchCurrentUser()
    }
  }

  return {
    // 状态
    token,
    user,
    loading,
    // 计算属性
    isLoggedIn,
    isAdmin,
    username,
    displayName,
    userRole,
    // 方法
    login,
    logout,
    fetchCurrentUser,
    updateProfile,
    changePassword,
    hasPermission,
    initializeAuth
  }
})
