<template>
  <div class="heatmap-page">
    <!-- 页面标签和报告按钮 -->
    <div class="page-tabs">
      <el-tag type="info" effect="plain" closable>库位分布</el-tag>
      
      <!-- 视图切换 -->
      <div class="view-switch">
        <el-button-group>
          <el-button type="primary">2D 视图</el-button>
          <el-button @click="$router.push('/heatmap3d')">3D 视图</el-button>
        </el-button-group>
      </div>
      
      <!-- 报告功能区 -->
      <div class="report-actions">
        <el-button 
          type="success" 
          @click="handleGenerateReport"
          :loading="reportLoading"
        >
          <el-icon><Document /></el-icon>
          生成分析报告
        </el-button>
        <el-dropdown v-if="reportList.length > 0" trigger="click" @command="handleDownloadReport">
          <el-button type="primary">
            <el-icon><Download /></el-icon>
            历史报告
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item 
                v-for="report in reportList" 
                :key="report.filename"
                :command="report.filename"
              >
                <div class="report-item">
                  <span class="report-name">{{ formatReportName(report.filename) }}</span>
                  <span class="report-size">{{ formatFileSize(report.size) }}</span>
                </div>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section card">
      <div class="filter-item">
        <span class="filter-label">仓库:</span>
        <el-select v-model="selectedWarehouse" placeholder="选择仓库" style="width: 140px" @change="handleWarehouseChange">
          <el-option
            v-for="wh in warehouses"
            :key="wh.id"
            :label="wh.name"
            :value="wh.id"
          />
        </el-select>
      </div>

      <div class="filter-item">
        <span class="filter-label">库区:</span>
        <el-select v-model="selectedZone" placeholder="默认库区" style="width: 140px">
          <el-option label="全部库区" :value="0" />
          <el-option
            v-for="zone in zones"
            :key="zone.id"
            :label="zone.name"
            :value="zone.id"
          />
        </el-select>
      </div>

      <div class="filter-item">
        <span class="filter-label">库位类型:</span>
        <el-select v-model="selectedShelfType" placeholder="启用" clearable style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="普通货架" value="normal" />
          <el-option label="高位货架" value="high_rack" />
          <el-option label="地堆" value="ground_stack" />
        </el-select>
      </div>

      <div class="filter-item">
        <el-radio-group v-model="timeRange" @change="handleTimeRangeChange">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="today">今天</el-radio-button>
          <el-radio-button value="7days">近7天</el-radio-button>
          <el-radio-button value="30days">近30天</el-radio-button>
        </el-radio-group>
      </div>

      <div class="filter-item">
        <span class="filter-label">时间段:</span>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 240px"
          @change="handleDateRangeChange"
        />
      </div>

      <div class="filter-actions">
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          查 询
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重 置
        </el-button>
      </div>
    </div>

    <!-- 热力图图例 -->
    <div class="heat-legend card">
      <span class="legend-label">0</span>
      <div class="legend-bar"></div>
      <span class="legend-label">{{ store.HEAT_COLOR_CAP }}+</span>
    </div>

    <!-- 热力图主体 - 使用与画布相同的网格布局 -->
    <div class="heatmap-content card" ref="heatmapContentRef" v-loading="loading">
      <div class="canvas-layout" v-if="heatmapData" :style="canvasGridStyle">
        <!-- 渲染每个单元格 -->
        <template v-for="cell in layoutCells" :key="`${cell.gridX}-${cell.gridY}`">
          <div 
            v-if="cell.shelf"
            class="layout-cell shelf-cell"
            :style="getCellPosition(cell)"
            @click.stop="handleShelfClick(cell.shelf)"
            @dblclick.stop="handleShelfDblClick(cell.shelf)"
            @mouseenter="handleCellMouseEnter($event, cell.shelf)"
            @mouseleave="handleMouseLeave"
          >
            <div 
              class="shelf-heat"
              :style="{ backgroundColor: getHeatColor(getShelfMaxHeat(cell.shelf.locations)) }"
              @mouseenter.stop="handleCellMouseEnter($event, cell.shelf)"
            >
              {{ getShelfDisplayLabel(cell.shelf) }}
            </div>
            <div class="shelf-label">{{ cell.shelf.shelf_name }}</div>
          </div>
          <div 
            v-else
            class="layout-cell empty-cell"
            :style="getCellPosition(cell)"
          ></div>
        </template>
      </div>

      <el-empty v-else description="暂无数据" />
    </div>

    <!-- 热度说明图例 -->
    <div class="combined-legend card">
      <div class="legend-group heat-legend-group">
        <span class="legend-title">热度说明：</span>
        <div class="legend-items">
          <div class="heat-gradient-bar">
            <span class="heat-label">冷门（低频）</span>
            <div class="gradient-bar"></div>
            <span class="heat-label">热门（高频）</span>
          </div>
          <div class="heat-tips">
            <span class="tip-item">· 颜色越深表示拣货频率越高</span>
            <span class="tip-item">· 数值范围：{{ minHeatValue }} - {{ maxHeatValue }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 库位详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="库位详情"
      width="400px"
    >
      <div class="location-detail-popup" v-if="selectedLocation">
        <div class="detail-item">
          <span class="label">库位编码</span>
          <span class="value">{{ selectedLocation.full_code }}</span>
        </div>
        <div class="detail-item">
          <span class="label">热度值</span>
          <span class="value">{{ selectedLocation.heat_value.toFixed(2) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">拣货频率</span>
          <span class="value">{{ selectedLocation.pick_frequency }} 次</span>
        </div>
        <div class="detail-item">
          <span class="label">周转率</span>
          <span class="value">{{ (selectedLocation.turnover_rate * 100).toFixed(1) }}%</span>
        </div>
        <div class="detail-item">
          <span class="label">当前库存</span>
          <span class="value">{{ selectedLocation.inventory_qty }} 件</span>
        </div>
      </div>
    </el-dialog>

    <!-- 编辑显示标识弹窗 -->
    <el-dialog
      v-model="editLabelDialogVisible"
      title="编辑显示标识"
      width="360px"
      :close-on-click-modal="false"
    >
      <div class="edit-label-form">
        <div class="form-item">
          <span class="label">货架名称：</span>
          <span class="value">{{ editingShelf?.shelf_name }}</span>
        </div>
        <div class="form-item">
          <span class="label">显示标识：</span>
          <el-input 
            v-model="editLabelValue" 
            placeholder="请输入显示标识"
            maxlength="50"
            show-word-limit
            @keyup.enter="handleSaveDisplayLabel"
          />
        </div>
        <div class="form-tip">
          <el-icon><InfoFilled /></el-icon>
          提示：显示标识将在热力图单元格中显示，方便快速识别
        </div>
      </div>
      <template #footer>
        <el-button @click="editLabelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveDisplayLabel" :loading="savingLabel">保存</el-button>
      </template>
    </el-dialog>

    <!-- 悬浮提示 -->
    <div 
      class="hover-tooltip" 
      v-show="tooltipVisible"
      :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
    >
      <template v-if="hoverLocation">
        <div><strong>{{ hoverLocation.full_code }}</strong></div>
        <div>热度: {{ hoverLocation.heat_value.toFixed(0) }}</div>
        <div>拣货: {{ hoverLocation.pick_frequency }} 次</div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useHeatmapStore } from '@/stores/heatmap'
import { warehouseApi, reportApi } from '@/api'
import type { LocationHeatItem, ShelfHeatData, ShelfType, TimeRange } from '@/types'
import type { ReportInfo } from '@/api'
import { ElMessage, ElNotification } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'

const store = useHeatmapStore()

// 报告相关状态
const reportLoading = ref(false)
const reportList = ref<ReportInfo[]>([])

// 筛选状态
const selectedWarehouse = ref<number | null>(null)
const selectedZone = ref<number | null>(null)
const selectedShelfType = ref<string>('')
const timeRange = ref<TimeRange>('all')
const dateRange = ref<[Date, Date] | null>(null)
const warehouses = ref<any[]>([])

// 弹窗状态
const detailDialogVisible = ref(false)
const selectedLocation = ref<LocationHeatItem | null>(null)

// 悬浮提示状态
const tooltipVisible = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)
const hoverLocation = ref<LocationHeatItem | null>(null)

// 编辑显示标识状态
const editLabelDialogVisible = ref(false)
const editingShelf = ref<ShelfHeatData | null>(null)
const editLabelValue = ref('')
const savingLabel = ref(false)

// 单击/双击区分
let clickTimer: ReturnType<typeof setTimeout> | null = null
const CLICK_DELAY = 250 // 毫秒

// 从 store 获取数据
const loading = computed(() => store.loading)
const heatmapData = computed(() => store.heatmapData)
const zones = computed(() => store.zones)
const maxHeatValue = computed(() => store.maxHeatValue)
const minHeatValue = computed(() => store.minHeatValue)

// 获取热力颜色
const getHeatColor = (value: number) => store.getHeatColor(value)

// 获取货架显示标识（优先使用 display_label，其次生成唯一标识）
const getShelfDisplayLabel = (shelf: any): string => {
  // 优先使用自定义的 display_label
  if (shelf.display_label) {
    return shelf.display_label
  }
  
  // 从 aisle_code 和 shelf_name 生成标识
  // 例如: aisle_code="01巷", shelf_name="地堆05" -> "01-05"
  let aisleNum = ''
  let shelfNum = ''
  
  // 提取巷道编号
  if (shelf.aisle_code) {
    const aisleMatch = shelf.aisle_code.match(/(\d+)/)
    if (aisleMatch) {
      aisleNum = aisleMatch[1].padStart(2, '0')
    }
  }
  
  // 提取货架编号
  if (shelf.shelf_name) {
    const shelfMatch = shelf.shelf_name.match(/(\d+)/)
    if (shelfMatch) {
      shelfNum = shelfMatch[1].padStart(2, '0')
    }
  }
  
  // 组合标识
  if (aisleNum && shelfNum) {
    return `${aisleNum}-${shelfNum}`
  }
  
  // 尝试从 full_code 提取
  if (shelf.locations && shelf.locations.length > 0 && shelf.locations[0].full_code) {
    const fullCode = shelf.locations[0].full_code
    const parts = fullCode.split('-')
    if (parts.length >= 3) {
      const aNum = parts[1].replace(/[^\d]/g, '')
      const sNum = parts[2].replace(/[^\d]/g, '')
      if (aNum && sNum) {
        return `${aNum.padStart(2, '0')}-${sNum.padStart(2, '0')}`
      }
    }
  }
  
  // 只有货架编号
  if (shelfNum) {
    return shelfNum
  }
  
  // 使用货架编码
  if (shelf.shelf_code) {
    return shelf.shelf_code
  }
  
  // 默认返回 "-"
  return '-'
}

// 获取货架类型颜色
const getShelfTypeColor = (type: ShelfType): string => {
  const colors: Record<ShelfType, string> = {
    normal: '#e31a1c',
    high_rack: '#fd8d3c',
    ground_stack: '#e31a1c',
    mezzanine: '#409eff',
    cantilever: '#67c23a'
  }
  return colors[type] || '#ddd'
}

// 网格单元格大小
const MIN_CELL_WIDTH = 24 // 最小宽度
const MIN_CELL_HEIGHT = 16 // 最小高度
const LABEL_HEIGHT = 12 // 底部标签高度
const GAP_SIZE = 1 // 间隙

// 容器引用
const heatmapContentRef = ref<HTMLElement | null>(null)

// 容器尺寸响应式变量
const containerWidth = ref(0)
const containerHeight = ref(0)

// ResizeObserver 实例
let resizeObserver: ResizeObserver | null = null

// 更新容器尺寸
const updateContainerSize = () => {
  if (heatmapContentRef.value) {
    containerWidth.value = heatmapContentRef.value.clientWidth
    containerHeight.value = heatmapContentRef.value.clientHeight
  } else {
    // 回退到窗口尺寸估算
    containerWidth.value = window.innerWidth - 60
    containerHeight.value = window.innerHeight - 300
  }
}

// 初始化 ResizeObserver
const initResizeObserver = () => {
  if (heatmapContentRef.value && !resizeObserver) {
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerWidth.value = entry.contentRect.width
        containerHeight.value = entry.contentRect.height
      }
    })
    resizeObserver.observe(heatmapContentRef.value)
  }
}

// 窗口 resize 处理（作为备用）
let resizeTimer: ReturnType<typeof setTimeout> | null = null
const handleWindowResize = () => {
  // 防抖处理
  if (resizeTimer) clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    updateContainerSize()
  }, 100)
}

// 计算货架的平均热力值
const getShelfAvgHeat = (locations: any[]) => {
  if (!locations || locations.length === 0) return 0
  const total = locations.reduce((sum, loc) => sum + (loc.heat_value || 0), 0)
  return total / locations.length
}

// 计算布局边界（包含最小值）
const getLayoutBounds = () => {
  if (!heatmapData.value) return { minX: 0, maxX: 0, minY: 0, maxY: 0 }
  let minX = Infinity, maxX = -Infinity
  let minY = Infinity, maxY = -Infinity
  
  heatmapData.value.aisles.forEach((aisle: any) => {
    if (aisle.y_coordinate < minY) minY = aisle.y_coordinate
    if (aisle.y_coordinate > maxY) maxY = aisle.y_coordinate
    aisle.shelves.forEach((shelf: any) => {
      if (shelf.x_coordinate < minX) minX = shelf.x_coordinate
      if (shelf.x_coordinate > maxX) maxX = shelf.x_coordinate
    })
  })
  
  // 处理空数据
  if (minX === Infinity) minX = 0
  if (maxX === -Infinity) maxX = 0
  if (minY === Infinity) minY = 0
  if (maxY === -Infinity) maxY = 0
  
  return { minX, maxX, minY, maxY }
}

// 计算自适应的单元格尺寸（宽高分开计算，响应容器大小变化）
const adaptiveCellDimensions = computed(() => {
  // 响应式依赖容器尺寸
  const availableWidth = containerWidth.value || (window.innerWidth - 60)
  const availableHeight = containerHeight.value || (window.innerHeight - 300)
  
  const { minX, maxX, minY, maxY } = getLayoutBounds()
  const cols = maxX - minX + 1
  const rows = maxY - minY + 1
  
  if (cols <= 0 || rows <= 0) {
    return { width: MIN_CELL_WIDTH, height: MIN_CELL_HEIGHT }
  }
  
  // 计算可用空间（减去内边距和间隙）
  const usableWidth = availableWidth - 40 // 左右内边距
  const usableHeight = availableHeight - 40 // 上下内边距
  
  // 分别计算宽度和高度，使内容完全适应屏幕
  let cellWidth = Math.floor((usableWidth - (cols - 1) * GAP_SIZE) / cols)
  let cellHeight = Math.floor((usableHeight - (rows - 1) * GAP_SIZE - rows * LABEL_HEIGHT) / rows)
  
  // 确保最小尺寸，不设置最大尺寸限制以实现全屏自适应
  cellWidth = Math.max(MIN_CELL_WIDTH, cellWidth)
  cellHeight = Math.max(MIN_CELL_HEIGHT, cellHeight)
  
  return { width: cellWidth, height: cellHeight }
})

// 画布网格样式（自适应全局展示，宽高独立）
const canvasGridStyle = computed(() => {
  const { minX, maxX, minY, maxY } = getLayoutBounds()
  const cols = maxX - minX + 1
  const rows = maxY - minY + 1
  const { width, height } = adaptiveCellDimensions.value
  
  return {
    display: 'grid',
    gridTemplateColumns: `repeat(${cols}, ${width}px)`,
    gridTemplateRows: `repeat(${rows}, ${height + LABEL_HEIGHT}px)`,
    gap: `${GAP_SIZE}px`,
    padding: '8px',
    justifyContent: 'center'
  }
})

// 生成布局单元格数据（只生成有效范围内的单元格）
const layoutCells = computed(() => {
  if (!heatmapData.value) return []
  
  const { minX, maxX, minY, maxY } = getLayoutBounds()
  const cells: Array<{ x: number; y: number; gridX: number; gridY: number; shelf: any | null }> = []
  
  // 创建货架位置映射
  const shelfMap = new Map<string, any>()
  heatmapData.value.aisles.forEach((aisle: any) => {
    aisle.shelves.forEach((shelf: any) => {
      const key = `${shelf.x_coordinate}-${aisle.y_coordinate}`
      shelfMap.set(key, { ...shelf, aisle_code: aisle.aisle_code })
    })
  })
  
  // 只生成有效范围内的单元格
  for (let y = minY; y <= maxY; y++) {
    for (let x = minX; x <= maxX; x++) {
      const key = `${x}-${y}`
      cells.push({
        x,
        y,
        gridX: x - minX, // 相对网格位置
        gridY: y - minY, // 相对网格位置
        shelf: shelfMap.get(key) || null
      })
    }
  }
  
  return cells
})

// 获取单元格位置样式
const getCellPosition = (cell: { gridX: number; gridY: number }) => {
  return {
    gridColumn: cell.gridX + 1,
    gridRow: cell.gridY + 1
  }
}

// 处理单击事件（延迟执行，避免与双击冲突）
const handleShelfClick = (shelf: any) => {
  // 如果有正在等待的点击，说明是双击，取消单击
  if (clickTimer) {
    clearTimeout(clickTimer)
    clickTimer = null
    return
  }
  
  // 延迟执行单击，等待可能的双击
  clickTimer = setTimeout(() => {
    clickTimer = null
    showShelfDetail(shelf)
  }, CLICK_DELAY)
}

// 处理双击事件
const handleShelfDblClick = (shelf: ShelfHeatData) => {
  // 取消可能正在等待的单击事件
  if (clickTimer) {
    clearTimeout(clickTimer)
    clickTimer = null
  }
  handleEditDisplayLabel(shelf)
}

// 显示货架详情（所有库位）
const showShelfDetail = (shelf: any) => {
  if (shelf.locations && shelf.locations.length > 0) {
    selectedLocation.value = shelf.locations[0]
    detailDialogVisible.value = true
  }
}

// 货架单元格悬浮
const handleCellMouseEnter = (event: MouseEvent, shelf: any) => {
  if (shelf.locations && shelf.locations.length > 0) {
    hoverLocation.value = shelf.locations[0]
    tooltipX.value = event.pageX + 10
    tooltipY.value = event.pageY + 10
    tooltipVisible.value = true
  }
}

// 获取货架的最大热力值
const getShelfMaxHeat = (locations: LocationHeatItem[] | undefined): number => {
  if (!locations || locations.length === 0) return 0
  return Math.max(...locations.map(loc => loc.heat_value || 0))
}

// 对库位进行排序（从上到下，从左到右，D-A行）
const getOrderedLocations = (shelf: ShelfHeatData): LocationHeatItem[] => {
  return [...shelf.locations].sort((a, b) => {
    // 先按行降序（D在上，A在下）
    if (a.row_index !== b.row_index) {
      return b.row_index - a.row_index
    }
    // 再按列升序
    return a.column_index - b.column_index
  })
}

// 显示库位详情
const showLocationDetail = (location: LocationHeatItem) => {
  selectedLocation.value = location
  detailDialogVisible.value = true
}

// 鼠标悬浮
const handleMouseEnter = (event: MouseEvent, location: LocationHeatItem) => {
  hoverLocation.value = location
  tooltipX.value = event.pageX + 10
  tooltipY.value = event.pageY + 10
  tooltipVisible.value = true
}

const handleMouseLeave = () => {
  tooltipVisible.value = false
  hoverLocation.value = null
}

// 打开编辑显示标识弹窗
const handleEditDisplayLabel = (shelf: ShelfHeatData) => {
  editingShelf.value = shelf
  // 使用当前显示的标识作为默认值
  editLabelValue.value = shelf.display_label || shelf.locations?.[0]?.location_code || shelf.shelf_code || ''
  editLabelDialogVisible.value = true
}

// 保存显示标识
const handleSaveDisplayLabel = async () => {
  if (!editingShelf.value) return
  
  const newLabel = editLabelValue.value.trim()
  if (!newLabel) {
    ElMessage.warning('显示标识不能为空')
    return
  }
  
  savingLabel.value = true
  try {
    await warehouseApi.updateShelfDisplayLabel(editingShelf.value.shelf_id, newLabel)
    
    // 更新本地数据
    editingShelf.value.display_label = newLabel
    
    ElMessage.success('显示标识已更新')
    editLabelDialogVisible.value = false
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    savingLabel.value = false
  }
}

// 时间范围变更
const handleTimeRangeChange = (value: TimeRange) => {
  dateRange.value = null
  store.setTimeRange(value)
}

// 自定义日期范围变更
const handleDateRangeChange = (value: [Date, Date] | null) => {
  if (value) {
    store.updateFilter({
      time_range: 'custom',
      start_date: value[0].toISOString(),
      end_date: value[1].toISOString()
    })
  }
}

// 查询
const handleSearch = () => {
  store.loadHeatmapData()
}

// 重置
const handleReset = () => {
  timeRange.value = 'today'
  dateRange.value = null
  selectedShelfType.value = ''
  store.updateFilter({
    time_range: 'all',
    shelf_type: undefined,
    start_date: undefined,
    end_date: undefined
  })
}

// 监听库区变化
watch(selectedZone, (newVal) => {
  if (newVal !== null) {
    store.setZone(newVal)
  }
})

// 监听货架类型变化
watch(selectedShelfType, (newVal) => {
  store.setShelfType(newVal as ShelfType || undefined)
})

// 加载仓库变更
const handleWarehouseChange = async (warehouseId: number) => {
  await store.loadZones(warehouseId)
  if (store.zones.length > 0) {
    selectedZone.value = store.zones[0].id
    await store.loadHeatmapData()
  } else {
    selectedZone.value = null
  }
}

// ==================== 报告功能 ====================

// 加载报告列表
const loadReportList = async () => {
  try {
    const result = await reportApi.getReportList()
    reportList.value = result.reports || []
  } catch (error) {
    console.error('加载报告列表失败:', error)
  }
}

// 生成报告
const handleGenerateReport = async () => {
  reportLoading.value = true
  try {
    const result = await reportApi.generateReport(selectedZone.value || undefined)
    if (result.success) {
      ElNotification({
        title: '报告生成成功',
        message: '正在下载分析报告...',
        type: 'success',
        duration: 3000
      })
      // 下载报告
      await handleDownloadReport(result.filename)
      // 刷新报告列表
      await loadReportList()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '报告生成失败')
  } finally {
    reportLoading.value = false
  }
}

// 下载报告
const handleDownloadReport = async (filename: string) => {
  try {
    const blob = await reportApi.downloadReport(filename)
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('报告下载成功')
  } catch (error) {
    ElMessage.error('报告下载失败')
  }
}

// 格式化报告名称
const formatReportName = (filename: string): string => {
  // heatmap_report_20260130_181551.docx -> 2026-01-30 18:15
  const match = filename.match(/heatmap_report_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})/)
  if (match) {
    return `${match[1]}-${match[2]}-${match[3]} ${match[4]}:${match[5]}`
  }
  return filename
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

// 初始化
onMounted(async () => {
  // 添加窗口 resize 事件监听
  window.addEventListener('resize', handleWindowResize)
  
  // 初始化容器尺寸和 ResizeObserver
  await nextTick()
  updateContainerSize()
  initResizeObserver()
  
  // 先加载仓库列表
  try {
    warehouses.value = await warehouseApi.getWarehouses()
    if (warehouses.value.length > 0) {
      // 默认选择第一个仓库
      selectedWarehouse.value = warehouses.value[0].id
      await store.loadZones(warehouses.value[0].id)
      if (store.zones.length > 0) {
        // 默认选择"全部库区"，这样可以看到所有库区的数据
        selectedZone.value = 0
        store.setZone(0)
      }
    }
    // 加载报告列表
    await loadReportList()
    
    // 数据加载后再次更新容器尺寸
    await nextTick()
    updateContainerSize()
  } catch (error) {
    console.error('初始化失败:', error)
  }
})

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleWindowResize)
  if (resizeTimer) clearTimeout(resizeTimer)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})
</script>

<style lang="scss" scoped>
.heatmap-page {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-tabs {
  flex-shrink: 0;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 20px;
  
  .view-switch {
    margin-left: 20px;
  }
  
  .report-actions {
    display: flex;
    gap: 10px;
    margin-left: auto;
  }
}

.report-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-width: 200px;
  
  .report-name {
    font-size: 13px;
  }
  
  .report-size {
    font-size: 12px;
    color: #909399;
    margin-left: 15px;
  }
}

.filter-section {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;

  .filter-item {
    display: flex;
    align-items: center;
    gap: 8px;

    .filter-label {
      font-size: 14px;
      color: #606266;
      white-space: nowrap;
    }
  }

  .filter-actions {
    margin-left: auto;
  }
}

.heat-legend {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 15px;

  .legend-bar {
    width: 300px;
    height: 16px;
    background: linear-gradient(to right, #ffffcc, #ffeda0, #fed976, #feb24c, #fd8d3c, #fc4e2a, #e31a1c, #bd0026, #800026);
    border-radius: 2px;
  }

  .legend-label {
    font-size: 12px;
    color: #666;
    min-width: 50px;
    text-align: center;
  }
}

.heatmap-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 10px;
}

.canvas-layout {
  background: #f5f7fa;
  border-radius: 6px;
  min-width: fit-content;
  margin: 0 auto;
}

.layout-cell {
  width: 100%;
  height: 100%;
  border-radius: 3px;
  transition: all 0.15s;
  box-sizing: border-box;
}

.empty-cell {
  width: 100%;
  height: 100%;
  background: #fff;
  border: 1px solid #e4e7ed;
  box-sizing: border-box;
}

.shelf-cell {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #409eff;
  border-radius: 3px;
  cursor: pointer;
  box-sizing: border-box;
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.5);
    z-index: 10;
  }
}

.shelf-heat {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  color: #333;
  cursor: pointer;
  overflow: hidden;
  padding: 1px;
  
  &:hover {
    outline: 1px solid #fff;
  }
}

.shelf-label {
  flex-shrink: 0;
  height: 12px;
  line-height: 12px;
  font-size: 9px;
  color: #fff;
  text-align: center;
  background: #409eff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 1px;
  box-sizing: border-box;
  border-radius: 0 0 2px 2px;
}

// 综合图例区域
.combined-legend {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding: 12px 20px;
  margin-top: 10px;
  background: #fff;
  border-radius: 6px;
  
  .legend-group {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    
    .legend-title {
      font-size: 13px;
      font-weight: 600;
      color: #303133;
      white-space: nowrap;
      line-height: 24px;
    }
    
    .legend-items {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }
  }
  
  // 热度说明
  .heat-legend-group {
    .legend-items {
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
    }
    
    .heat-gradient-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .heat-label {
        font-size: 11px;
        color: #909399;
        white-space: nowrap;
      }
      
      .gradient-bar {
        width: 120px;
        height: 12px;
        border-radius: 6px;
        background: linear-gradient(to right, 
          #ffffcc 0%, 
          #ffeda0 20%, 
          #fed976 40%, 
          #feb24c 60%, 
          #fd8d3c 80%, 
          #e31a1c 100%
        );
        border: 1px solid rgba(0,0,0,0.1);
      }
    }
    
    .heat-tips {
      display: flex;
      gap: 15px;
      
      .tip-item {
        font-size: 11px;
        color: #909399;
      }
    }
  }
}

.hover-tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 9999;
  pointer-events: none;

  div {
    line-height: 1.6;
  }
}

// 编辑显示标识弹窗
.edit-label-form {
  .form-item {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    
    .label {
      width: 80px;
      flex-shrink: 0;
      color: #606266;
      font-size: 14px;
    }
    
    .value {
      color: #303133;
      font-weight: 500;
    }
  }
  
  .form-tip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 12px;
    background: #f4f4f5;
    border-radius: 4px;
    font-size: 12px;
    color: #909399;
    
    .el-icon {
      color: #909399;
    }
  }
}
</style>
