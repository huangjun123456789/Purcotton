// 货架类型
export type ShelfType = 'normal' | 'high_rack' | 'ground_stack' | 'mezzanine' | 'cantilever'

// 时间范围
export type TimeRange = 'all' | 'today' | '7days' | '30days' | 'custom'

// ==================== 用户相关 ====================

// 用户角色
export type UserRole = 'admin' | 'user'

// 用户信息
export interface User {
  id: number
  username: string
  nickname?: string
  email?: string
  phone?: string
  role: UserRole
  is_active: boolean
  last_login?: string
  created_at: string
  updated_at: string
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

// 创建用户请求
export interface CreateUserRequest {
  username: string
  password: string
  nickname?: string
  email?: string
  phone?: string
  role: UserRole
}

// 更新用户请求
export interface UpdateUserRequest {
  nickname?: string
  email?: string
  phone?: string
  role?: UserRole
  is_active?: boolean
}

// 修改密码请求
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

// 重置密码请求
export interface ResetPasswordRequest {
  new_password: string
}

// 用户个人资料更新
export interface UserProfileUpdate {
  nickname?: string
  email?: string
  phone?: string
}

// 仓库
export interface Warehouse {
  id: number
  code: string
  name: string
  address?: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 库区
export interface Zone {
  id: number
  warehouse_id: number
  code: string
  name: string
  description?: string
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 通道
export interface Aisle {
  id: number
  zone_id: number
  code: string
  name: string
  y_coordinate: number
  sort_order: number
  is_active: boolean
}

// 货架
export interface Shelf {
  id: number
  aisle_id: number
  code: string
  name: string
  shelf_type: ShelfType
  rows: number
  columns: number
  layers: number  // 层数
  x_coordinate: number
  sort_order: number
  is_active: boolean
}

// 库位热度项
export interface LocationHeatItem {
  location_id: number
  location_code: string
  full_code: string
  row_label: string
  column_number: number
  row_index: number
  column_index: number
  heat_value: number
  pick_frequency: number
  turnover_rate: number
  inventory_qty: number
}

// 货架热度数据
export interface ShelfHeatData {
  shelf_id: number
  shelf_code: string
  shelf_name: string
  display_label?: string
  shelf_type: ShelfType
  x_coordinate: number
  rows: number
  columns: number
  layers: number  // 层数
  locations: LocationHeatItem[]
}

// 通道热度数据
export interface AisleHeatData {
  aisle_id: number
  aisle_code: string
  aisle_name: string
  y_coordinate: number
  shelves: ShelfHeatData[]
}

// 热力图响应数据
export interface HeatmapData {
  zone_id: number
  zone_code: string
  zone_name: string
  aisles: AisleHeatData[]
  min_heat: number
  max_heat: number
  time_range: TimeRange
  start_date: string
  end_date: string
}

// 筛选参数
export interface HeatmapFilterParams {
  zone_id?: number
  shelf_type?: ShelfType
  time_range: TimeRange
  start_date?: string
  end_date?: string
}

// 导入结果
export interface ImportResult {
  success: boolean
  total_rows: number
  imported_rows: number
  skipped_rows?: number  // 跳过的行数（库位不存在）
  failed_rows: number
  errors?: string[]
  date_range?: {
    start_date: string
    end_date: string
  }
}

// 画布单元格类型
export type CellType = 'empty' | 'shelf' | 'aisle' | 'wall'

// 画布单元格
export interface CanvasCell {
  x: number           // 列索引
  y: number           // 行索引
  type: CellType
  zoneId?: string     // 所属库区唯一ID
  shelfConfig?: {     // 货架配置
    rows: number
    columns: number
    layers: number    // 层数
    shelfType: ShelfType
  }
}

// 库区定义
export interface CanvasZone {
  id: string          // 唯一标识符
  code: string        // 库区代码（用于显示和保存）
  name: string
  color: string
}
