import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, UserProfileUpdate } from '@/types'
import { authApi } from '@/api'

// Token 存储 key
const TOKEN_KEY = 'access_token'
const USER_KEY = 'user_info'
const GUEST_KEY = 'is_guest'

// 访客用户信息
const GUEST_USER: User = {
  id: 0,
  username: 'guest',
  nickname: '访客用户',
  role: 'user',
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
  const loading = ref(false)
  const isGuest = ref(localStorage.getItem(GUEST_KEY) === 'true')

  // 计算属性
  const isLoggedIn = computed(() => (!!token.value && !!user.value) || isGuest.value)
  const isAdmin = computed(() => !isGuest.value && user.value?.role === 'admin')
  const username = computed(() => user.value?.username || '')
  const displayName = computed(() => {
    if (isGuest.value) return '访客用户'
    return user.value?.nickname || user.value?.username || '用户'
  })
  const userRole = computed(() => {
    if (isGuest.value) return 'user'
    return user.value?.role || 'user'
  })

  // 管理员登录
  const login = async (loginData: LoginRequest): Promise<boolean> => {
    loading.value = true
    try {
      const response = await authApi.login(loginData)
      
      // 清除访客状态
      isGuest.value = false
      localStorage.removeItem(GUEST_KEY)
      
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

  // 访客模式登录（普通用户）
  const loginAsGuest = () => {
    // 清除之前的登录状态
    token.value = null
    localStorage.removeItem(TOKEN_KEY)
    
    // 设置访客状态
    isGuest.value = true
    user.value = { ...GUEST_USER }
    
    localStorage.setItem(GUEST_KEY, 'true')
    localStorage.setItem(USER_KEY, JSON.stringify(GUEST_USER))
  }

  // 退出登录
  const logout = async () => {
    // 如果是访客模式，直接清除状态
    if (isGuest.value) {
      isGuest.value = false
      user.value = null
      localStorage.removeItem(GUEST_KEY)
      localStorage.removeItem(USER_KEY)
      return
    }
    
    try {
      await authApi.logout()
    } catch (error) {
      console.error('退出登录失败:', error)
    } finally {
      // 无论请求是否成功，都清除本地状态
      token.value = null
      user.value = null
      isGuest.value = false
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      localStorage.removeItem(GUEST_KEY)
    }
  }

  // 获取当前用户信息
  const fetchCurrentUser = async (): Promise<User | null> => {
    // 访客模式不需要获取用户信息
    if (isGuest.value) {
      return user.value
    }
    
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
    isGuest,
    // 计算属性
    isLoggedIn,
    isAdmin,
    username,
    displayName,
    userRole,
    // 方法
    login,
    loginAsGuest,
    logout,
    fetchCurrentUser,
    updateProfile,
    changePassword,
    hasPermission,
    initializeAuth
  }
})
