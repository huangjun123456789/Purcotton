import axios from 'axios'
import type { 
  Warehouse, Zone, Aisle, Shelf, 
  HeatmapData, HeatmapFilterParams, ImportResult,
  User, LoginRequest, LoginResponse, 
  CreateUserRequest, UpdateUserRequest,
  ChangePasswordRequest, ResetPasswordRequest, UserProfileUpdate
} from '@/types'

// Token 存储 key
const TOKEN_KEY = 'access_token'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动附加 Token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    // 401 未授权，清除 token 并跳转登录
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      // 避免在登录页循环跳转
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ==================== 认证 API ====================

export const authApi = {
  // 登录
  login: (data: LoginRequest): Promise<LoginResponse> =>
    api.post('/auth/login', data),
  
  // 获取当前用户信息
  getCurrentUser: (): Promise<User> =>
    api.get('/auth/me'),
  
  // 更新个人资料
  updateProfile: (data: UserProfileUpdate): Promise<User> =>
    api.put('/auth/me', data),
  
  // 修改密码
  changePassword: (data: ChangePasswordRequest): Promise<{ message: string }> =>
    api.post('/auth/change-password', data),
  
  // 退出登录
  logout: (): Promise<{ message: string }> =>
    api.post('/auth/logout')
}

// ==================== 用户管理 API ====================

export const userApi = {
  // 获取用户列表
  getUsers: (params?: {
    skip?: number
    limit?: number
    role?: string
    is_active?: boolean
    keyword?: string
  }): Promise<User[]> =>
    api.get('/users', { params }),
  
  // 获取用户数量
  getUsersCount: (params?: {
    role?: string
    is_active?: boolean
    keyword?: string
  }): Promise<{ count: number }> =>
    api.get('/users/count', { params }),
  
  // 创建用户
  createUser: (data: CreateUserRequest): Promise<User> =>
    api.post('/users', data),
  
  // 获取用户详情
  getUser: (id: number): Promise<User> =>
    api.get(`/users/${id}`),
  
  // 更新用户
  updateUser: (id: number, data: UpdateUserRequest): Promise<User> =>
    api.put(`/users/${id}`, data),
  
  // 删除用户
  deleteUser: (id: number): Promise<void> =>
    api.delete(`/users/${id}`),
  
  // 重置用户密码
  resetPassword: (id: number, data: ResetPasswordRequest): Promise<{ message: string }> =>
    api.post(`/users/${id}/reset-password`, data),
  
  // 切换用户状态
  toggleUserActive: (id: number): Promise<User> =>
    api.post(`/users/${id}/toggle-active`)
}

// ==================== 仓库管理 ====================

export const warehouseApi = {
  // 获取仓库列表
  getWarehouses: (isActive = true): Promise<Warehouse[]> => 
    api.get('/warehouse/', { params: { is_active: isActive } }),
  
  // 获取单个仓库
  getWarehouse: (id: number): Promise<Warehouse> => 
    api.get(`/warehouse/${id}`),
  
  // 创建仓库
  createWarehouse: (data: Partial<Warehouse>): Promise<Warehouse> => 
    api.post('/warehouse/', data),
  
  // 更新仓库
  updateWarehouse: (id: number, data: Partial<Warehouse>): Promise<Warehouse> => 
    api.put(`/warehouse/${id}`, data),
  
  // 获取库区列表
  getZones: (warehouseId: number): Promise<Zone[]> => 
    api.get(`/warehouse/${warehouseId}/zones`),
  
  // 创建库区
  createZone: (data: Partial<Zone>): Promise<Zone> => 
    api.post('/warehouse/zone', data),
  
  // 获取通道列表
  getAisles: (zoneId: number): Promise<Aisle[]> => 
    api.get(`/warehouse/zone/${zoneId}/aisles`),
  
  // 获取货架列表
  getShelves: (aisleId: number, shelfType?: string): Promise<Shelf[]> => 
    api.get(`/warehouse/aisle/${aisleId}/shelves`, { params: { shelf_type: shelfType } }),
  
  // 更新货架显示标识
  updateShelfDisplayLabel: (shelfId: number, displayLabel: string): Promise<Shelf> =>
    api.put(`/warehouse/shelf/${shelfId}/display-label`, { display_label: displayLabel }),
  
  // 批量设置仓库布局
  setupWarehouseLayout: (
    warehouseCode: string, 
    warehouseName: string, 
    zonesConfig: any[]
  ): Promise<Warehouse> => 
    api.post('/warehouse/setup', zonesConfig, {
      params: { warehouse_code: warehouseCode, warehouse_name: warehouseName }
    }),
  
  // 获取仓库布局数据（用于画布编辑器加载）
  getWarehouseLayout: (warehouseId: number): Promise<any> =>
    api.get(`/warehouse/${warehouseId}/layout`)
}

// ==================== 热力图 ====================

export const heatmapApi = {
  // 获取热力图数据
  getHeatmapData: (zoneId: number, params: HeatmapFilterParams): Promise<HeatmapData> => 
    api.get(`/heatmap/zone/${zoneId}`, { 
      params: {
        time_range: params.time_range,
        shelf_type: params.shelf_type,
        start_date: params.start_date,
        end_date: params.end_date
      }
    }),
  
  // 更新单个库位热度
  updateHeatData: (
    locationId: number,
    date: string,
    pickFrequency: number,
    turnoverRate?: number,
    inventoryQty?: number
  ): Promise<any> => 
    api.post('/heatmap/update', null, {
      params: {
        location_id: locationId,
        date,
        pick_frequency: pickFrequency,
        turnover_rate: turnoverRate,
        inventory_qty: inventoryQty
      }
    }),
  
  // 批量更新热度数据
  batchUpdateHeatData: (dataList: any[]): Promise<any> => 
    api.post('/heatmap/batch-update', dataList)
}

// ==================== 数据导入 ====================

export interface ImportHistoryItem {
  id: number
  filename: string
  file_type: string
  total_rows: number
  success_rows: number
  failed_rows: number
  status: 'success' | 'partial' | 'failed'
  errors: string[] | null
  import_time: string
}

export const importApi = {
  // 导入 Excel
  importExcel: (file: File): Promise<ImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 导入 CSV
  importCsv: (file: File): Promise<ImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/import/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 下载 Excel 模板
  downloadExcelTemplate: (): Promise<Blob> => 
    api.get('/import/template/excel', { responseType: 'blob' }),
  
  // 下载 CSV 模板
  downloadCsvTemplate: (): Promise<Blob> => 
    api.get('/import/template/csv', { responseType: 'blob' }),
  
  // 获取导入历史记录
  getImportHistory: (limit: number = 20): Promise<ImportHistoryItem[]> =>
    api.get('/import/history', { params: { limit } })
}

// ==================== 分析报告 ====================

export interface ReportInfo {
  filename: string
  size: number
  created_at: string
}

export interface GenerateReportResult {
  success: boolean
  filename: string
  message: string
}

export const reportApi = {
  // 生成分析报告
  generateReport: (zoneId?: number): Promise<GenerateReportResult> => 
    api.get('/report/generate', { params: { zone_id: zoneId } }),
  
  // 获取报告列表
  getReportList: (): Promise<{ reports: ReportInfo[] }> => 
    api.get('/report/list'),
  
  // 下载报告
  downloadReport: (filename: string): Promise<Blob> => 
    api.get(`/report/download/${filename}`, { responseType: 'blob' }),
  
  // 获取下载URL
  getDownloadUrl: (filename: string): string => 
    `${api.defaults.baseURL}/report/download/${filename}`
}

export default api
