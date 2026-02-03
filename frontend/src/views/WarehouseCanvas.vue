<template>
  <div class="canvas-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-divider direction="vertical" />
        <span class="warehouse-name">{{ warehouse?.name || '加载中...' }}</span>
      </div>
      
      <div class="toolbar-center">
        <el-radio-group v-model="currentTool" size="default">
          <el-radio-button value="select">
            <el-icon><Select /></el-icon>
            选择
          </el-radio-button>
          <el-radio-button value="shelf">
            <el-icon><Grid /></el-icon>
            货架
          </el-radio-button>
          <el-radio-button value="aisle">
            <el-icon><Guide /></el-icon>
            通道
          </el-radio-button>
          <el-radio-button value="eraser">
            <el-icon><Delete /></el-icon>
            橡皮擦
          </el-radio-button>
        </el-radio-group>
        
        <el-divider direction="vertical" />
        
        <span class="grid-size-label">网格大小:</span>
        <el-input-number 
          v-model="gridCols" 
          :min="5" 
          :max="50" 
          size="small"
          @change="resizeGrid"
        />
        <span>×</span>
        <el-input-number 
          v-model="gridRows" 
          :min="5" 
          :max="50" 
          size="small"
          @change="resizeGrid"
        />
      </div>
      
      <div class="toolbar-right">
        <el-tag v-if="hasUnsavedChanges" type="warning" size="small" class="unsaved-tag">
          未保存
        </el-tag>
        <el-button @click="clearCanvas">
          <el-icon><RefreshLeft /></el-icon>
          清空
        </el-button>
        <el-button type="primary" @click="saveLayout" :loading="saving">
          <el-icon><Check /></el-icon>
          保存布局
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧属性面板 -->
      <div class="left-panel">
        <el-card class="panel-card">
          <template #header>
            <div class="shelf-header">
              <span>货架属性</span>
              <el-tag v-if="selectedCell && selectedCell.type === 'shelf'" type="success" size="small">
                已选中
              </el-tag>
            </div>
          </template>
          <el-form label-width="70px" size="small">
            <el-form-item label="行数">
              <el-input-number v-model="shelfConfig.rows" :min="1" :max="26" />
            </el-form-item>
            <el-form-item label="列数">
              <el-input-number v-model="shelfConfig.columns" :min="1" :max="20" />
            </el-form-item>
            <el-form-item label="层数">
              <el-input-number v-model="shelfConfig.layers" :min="1" :max="10" />
              <el-tooltip content="货架的垂直层数，在3D视图中展示" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="shelfConfig.shelfType" style="width: 100%">
                <el-option label="普通货架" value="normal" />
                <el-option label="高位货架" value="high_rack" />
                <el-option label="地堆" value="ground_stack" />
              </el-select>
            </el-form-item>
          </el-form>
          <div v-if="selectedCell && selectedCell.type === 'shelf'" class="selected-info">
            <span>位置: ({{ selectedCell.x }}, {{ selectedCell.y }})</span>
            <span>库区: {{ getZoneNameById(selectedCell.zoneId) }}</span>
          </div>
        </el-card>

        <el-card class="panel-card">
          <template #header>
            <div class="zone-header">
              <span>库区管理</span>
              <el-button type="primary" link size="small" @click="addZone">
                <el-icon><Plus /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="zone-filter">
            <el-checkbox v-model="showAllZones" size="small">
              显示全部库区
            </el-checkbox>
          </div>
          <div class="zone-list">
            <div 
              v-for="(zone, index) in zones" 
              :key="index"
              class="zone-item"
              :class="{ active: currentZoneIndex === index }"
              @click="selectZone(index)"
            >
              <span 
                class="zone-color" 
                :style="{ backgroundColor: zone.color }"
              ></span>
              <el-input 
                v-model="zone.name" 
                size="small" 
                style="width: 80px"
                @click.stop
              />
              <el-button 
                type="danger" 
                link 
                size="small"
                @click.stop="removeZone(index)"
                v-if="zones.length > 1"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card">
          <template #header>
            <span>图例 <el-text type="info" size="small">(点击选择)</el-text></span>
          </template>
          <div class="legend">
            <div 
              class="legend-item clickable" 
              :class="{ active: currentTool === 'shelf' && shelfConfig.shelfType === 'normal' }"
              @click="selectShelfType('normal')"
            >
              <span class="legend-color shelf">S</span>
              <span>普通货架</span>
            </div>
            <div 
              class="legend-item clickable" 
              :class="{ active: currentTool === 'shelf' && shelfConfig.shelfType === 'high_rack' }"
              @click="selectShelfType('high_rack')"
            >
              <span class="legend-color shelf">H</span>
              <span>高位货架</span>
            </div>
            <div 
              class="legend-item clickable" 
              :class="{ active: currentTool === 'shelf' && shelfConfig.shelfType === 'ground_stack' }"
              @click="selectShelfType('ground_stack')"
            >
              <span class="legend-color shelf">G</span>
              <span>地堆</span>
            </div>
            <div 
              class="legend-item clickable" 
              :class="{ active: currentTool === 'aisle' }"
              @click="selectAisleTool"
            >
              <span class="legend-color aisle"></span>
              <span>通道</span>
            </div>
            <div 
              class="legend-item clickable" 
              :class="{ active: currentTool === 'eraser' }"
              @click="currentTool = 'eraser'"
            >
              <span class="legend-color empty"></span>
              <span>橡皮擦</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 中间画布区域 -->
      <div class="canvas-container" ref="canvasContainer">
        <div class="canvas-zone-indicator" v-if="!showAllZones">
          <span class="zone-indicator-color" :style="{ backgroundColor: currentZoneColor }"></span>
          <span>当前库区: {{ currentZoneName }}</span>
        </div>
        
        <!-- 画布包装器，用于放置扩展按钮 -->
        <div class="canvas-wrapper">
          <!-- 顶部按钮组 -->
          <div class="btn-group btn-group-top">
            <div class="expand-btn" @click="shrinkCanvas('top')" title="向上收缩" :class="{ disabled: !canShrink('top') }">
              <el-icon><Minus /></el-icon>
            </div>
            <div class="expand-btn" @click="expandCanvas('top')" title="向上扩展">
              <el-icon><Plus /></el-icon>
            </div>
          </div>
          
          <!-- 左侧按钮组 -->
          <div class="btn-group btn-group-left">
            <div class="expand-btn" @click="shrinkCanvas('left')" title="向左收缩" :class="{ disabled: !canShrink('left') }">
              <el-icon><Minus /></el-icon>
            </div>
            <div class="expand-btn" @click="expandCanvas('left')" title="向左扩展">
              <el-icon><Plus /></el-icon>
            </div>
          </div>
          
          <!-- 画布网格 -->
          <div 
            class="canvas-grid"
            ref="canvasGridRef"
            :style="gridStyle"
            @mousedown="handleCanvasMouseDown"
            @mousemove="handleCanvasMouseMove"
            @mouseup="handleCanvasMouseUp"
            @mouseleave="handleCanvasMouseLeave"
          >
            <div
              v-for="cell in displayCells"
              :key="`${cell.x}-${cell.y}`"
              class="grid-cell"
              :class="getCellClass(cell)"
              :style="getCellStyle(cell)"
              :data-x="cell.x"
              :data-y="cell.y"
            >
              <span v-if="cell.type === 'shelf'" class="cell-label">{{ getShelfLabel(cell) }}</span>
              <span v-else-if="cell.type === 'aisle'" class="cell-label">A</span>
            </div>
            
            <!-- 框选矩形 -->
            <div 
              v-if="isSelecting" 
              class="selection-box"
              :style="selectionBoxStyle"
            ></div>
            
            <!-- 拖拽预览 -->
            <div 
              v-for="preview in dragPreviewCells"
              :key="`preview-${preview.x}-${preview.y}`"
              class="drag-preview-cell"
              :style="getDragPreviewStyle(preview)"
            ></div>
            
            <!-- 粘贴预览 -->
            <div 
              v-for="preview in pastePreviewCells"
              :key="`paste-${preview.x}-${preview.y}`"
              class="paste-preview-cell"
              :style="getPastePreviewStyle(preview)"
            ></div>
          </div>
          
          <!-- 右侧按钮组 -->
          <div class="btn-group btn-group-right">
            <div class="expand-btn" @click="expandCanvas('right')" title="向右扩展">
              <el-icon><Plus /></el-icon>
            </div>
            <div class="expand-btn" @click="shrinkCanvas('right')" title="向右收缩" :class="{ disabled: !canShrink('right') }">
              <el-icon><Minus /></el-icon>
            </div>
          </div>
          
          <!-- 底部按钮组 -->
          <div class="btn-group btn-group-bottom">
            <div class="expand-btn" @click="expandCanvas('bottom')" title="向下扩展">
              <el-icon><Plus /></el-icon>
            </div>
            <div class="expand-btn" @click="shrinkCanvas('bottom')" title="向下收缩" :class="{ disabled: !canShrink('bottom') }">
              <el-icon><Minus /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧统计面板 -->
      <div class="right-panel">
        <el-card class="panel-card">
          <template #header>
            <div class="stats-header">
              <span>布局统计</span>
              <el-tag size="small" :type="showAllZones ? 'info' : 'primary'">
                {{ showAllZones ? '全部' : currentZoneName }}
              </el-tag>
            </div>
          </template>
          <div class="stats">
            <div class="stat-item">
              <span class="stat-label">货架数量</span>
              <span class="stat-value">{{ shelfCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">通道数量</span>
              <span class="stat-value">{{ aisleCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">预计库位</span>
              <span class="stat-value">{{ estimatedLocations }}</span>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card">
          <template #header>
            <span>操作提示</span>
          </template>
          <div class="tips">
            <p>1. 选择工具后点击或拖拽绘制</p>
            <p>2. 左侧设置货架属性</p>
            <p>3. 选择库区后绘制可分配区域</p>
            <p>4. 完成后点击保存布局</p>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { warehouseApi } from '@/api'
import type { Warehouse, CanvasCell, CanvasZone, ShelfType, CellType } from '@/types'

const route = useRoute()
const router = useRouter()

// 仓库信息
const warehouse = ref<Warehouse | null>(null)
const warehouseId = computed(() => Number(route.params.id))

// 工具状态
const currentTool = ref<'select' | 'shelf' | 'aisle' | 'eraser'>('shelf')
const currentZoneIndex = ref(0) // 使用索引追踪选中的库区
const showAllZones = ref(true) // 默认显示全部库区

// 生成唯一ID
const generateZoneId = () => `zone_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

// 当前选中的库区ID（用于绘制和过滤）
const currentZoneId = computed(() => zones.value[currentZoneIndex.value]?.id || '')

// 当前选中的库区代码（用于显示）
const currentZone = computed(() => zones.value[currentZoneIndex.value]?.code || 'A')

// 网格配置（工具栏设置值）
const gridRows = ref(20)
const gridCols = ref(30)

// 画布实际大小（边缘扩展/收缩使用）
const actualRows = ref(20)
const actualCols = ref(30)

// 选中的单元格（单选）
const selectedCell = ref<CanvasCell | null>(null)

// 多选状态
const selectedCells = ref<CanvasCell[]>([])  // 多选的单元格列表

// 框选状态
const isSelecting = ref(false)               // 是否正在框选
const selectionStart = ref({ x: 0, y: 0 })   // 框选起点（相对于画布容器的像素坐标）
const selectionEnd = ref({ x: 0, y: 0 })     // 框选终点（相对于画布容器的像素坐标）
const canvasContainerRef = ref<HTMLElement | null>(null)  // 画布容器引用
const canvasGridRef = ref<HTMLElement | null>(null)       // 画布网格引用

// 剪贴板
const clipboard = ref<CanvasCell[]>([])      // 复制的单元格数据
const clipboardOffset = ref({ x: 0, y: 0 })  // 剪贴板基准偏移（选中区域的最小 x, y）
const isCut = ref(false)                     // 是否是剪切操作

// 拖拽移动状态
const isDraggingSelection = ref(false)       // 是否正在拖拽移动选中区域
const dragStartGrid = ref({ x: 0, y: 0 })    // 拖拽起点（网格坐标）
const dragCurrentGrid = ref({ x: 0, y: 0 })  // 当前拖拽位置（网格坐标）

// 粘贴预览位置
const pastePreviewPos = ref<{ x: number, y: number } | null>(null)

// 从 localStorage 读取上次的货架配置
const getStoredShelfConfig = () => {
  try {
    const stored = localStorage.getItem('canvasShelfConfig')
    if (stored) {
      const config = JSON.parse(stored)
      // 确保 layers 字段存在
      return {
        rows: config.rows || 4,
        columns: config.columns || 5,
        layers: config.layers || 1,
        shelfType: config.shelfType || 'normal'
      }
    }
  } catch (e) {
    console.error('读取货架配置失败:', e)
  }
  return {
    rows: 4,
    columns: 5,
    layers: 1,
    shelfType: 'normal' as ShelfType
  }
}

// 货架配置
const shelfConfig = reactive(getStoredShelfConfig())

// 保存货架配置到 localStorage
const saveShelfConfig = () => {
  try {
    localStorage.setItem('canvasShelfConfig', JSON.stringify({
      rows: shelfConfig.rows,
      columns: shelfConfig.columns,
      layers: shelfConfig.layers,
      shelfType: shelfConfig.shelfType
    }))
  } catch (e) {
    console.error('保存货架配置失败:', e)
  }
}

// 库区列表
const zones = ref<CanvasZone[]>([
  { id: 'zone_init_A', code: 'A', name: 'A库区', color: '#409eff' }
])

// 画布数据
const cells = ref<CanvasCell[]>([])

// 绘制状态
const isDrawing = ref(false)
const saving = ref(false)
const hasUnsavedChanges = ref(false)  // 追踪未保存的修改
const isInitialLoad = ref(true)  // 是否正在初始加载

// 库区颜色列表
const zoneColors = [
  '#409eff', '#67c23a', '#e6a23c', '#f56c6c', 
  '#909399', '#9c27b0', '#00bcd4', '#ff9800'
]

// 初始化网格
const initGrid = () => {
  // 同步实际大小为设置值
  actualRows.value = gridRows.value
  actualCols.value = gridCols.value
  
  const newCells: CanvasCell[] = []
  for (let y = 0; y < actualRows.value; y++) {
    for (let x = 0; x < actualCols.value; x++) {
      newCells.push({
        x,
        y,
        type: 'empty',
        zoneId: undefined,
        shelfConfig: undefined
      })
    }
  }
  cells.value = newCells
}

// 调整网格大小（从工具栏触发）
const resizeGrid = () => {
  const oldCells = [...cells.value]
  
  // 同步实际大小为设置值
  actualRows.value = gridRows.value
  actualCols.value = gridCols.value
  
  // 重新初始化网格
  const newCells: CanvasCell[] = []
  for (let y = 0; y < actualRows.value; y++) {
    for (let x = 0; x < actualCols.value; x++) {
      newCells.push({
        x,
        y,
        type: 'empty',
        zoneId: undefined,
        shelfConfig: undefined
      })
    }
  }
  cells.value = newCells
  
  // 保留原有数据
  oldCells.forEach(oldCell => {
    if (oldCell.x < actualCols.value && oldCell.y < actualRows.value) {
      const idx = oldCell.y * actualCols.value + oldCell.x
      if (cells.value[idx]) {
        cells.value[idx] = oldCell
      }
    }
  })
}

// 扩展画布（不影响工具栏的网格大小设置）
const expandCanvas = (direction: 'top' | 'bottom' | 'left' | 'right') => {
  const expandSize = 1 // 每次扩展1行/列
  
  hasUnsavedChanges.value = true
  
  switch (direction) {
    case 'top':
      // 向上扩展：增加行数，所有现有元素 y 坐标 +expandSize
      actualRows.value += expandSize
      // 先更新所有现有单元格的 y 坐标
      cells.value.forEach(cell => {
        cell.y += expandSize
      })
      // 在顶部添加新的空白行
      const topNewCells: CanvasCell[] = []
      for (let y = 0; y < expandSize; y++) {
        for (let x = 0; x < actualCols.value; x++) {
          topNewCells.push({
            x,
            y,
            type: 'empty',
            zoneId: undefined,
            shelfConfig: undefined
          })
        }
      }
      cells.value = [...topNewCells, ...cells.value]
      break
      
    case 'bottom':
      // 向下扩展：增加行数，在底部添加新行
      const oldRows = actualRows.value
      actualRows.value += expandSize
      for (let y = oldRows; y < actualRows.value; y++) {
        for (let x = 0; x < actualCols.value; x++) {
          cells.value.push({
            x,
            y,
            type: 'empty',
            zoneId: undefined,
            shelfConfig: undefined
          })
        }
      }
      break
      
    case 'left':
      // 向左扩展：增加列数，所有现有元素 x 坐标 +expandSize
      actualCols.value += expandSize
      // 先更新所有现有单元格的 x 坐标
      cells.value.forEach(cell => {
        cell.x += expandSize
      })
      // 在左侧添加新的空白列
      const leftNewCells: CanvasCell[] = []
      for (let y = 0; y < actualRows.value; y++) {
        for (let x = 0; x < expandSize; x++) {
          leftNewCells.push({
            x,
            y,
            type: 'empty',
            zoneId: undefined,
            shelfConfig: undefined
          })
        }
      }
      // 需要按正确顺序插入
      const mergedCellsLeft: CanvasCell[] = []
      for (let y = 0; y < actualRows.value; y++) {
        // 先添加新列
        for (let x = 0; x < expandSize; x++) {
          mergedCellsLeft.push(leftNewCells.find(c => c.x === x && c.y === y)!)
        }
        // 再添加原有列
        for (let x = expandSize; x < actualCols.value; x++) {
          const originalCell = cells.value.find(c => c.x === x && c.y === y)
          if (originalCell) {
            mergedCellsLeft.push(originalCell)
          }
        }
      }
      cells.value = mergedCellsLeft
      break
      
    case 'right':
      // 向右扩展：增加列数，在右侧添加新列
      const oldCols = actualCols.value
      actualCols.value += expandSize
      // 在每行末尾添加新的单元格
      const rightNewCells: CanvasCell[] = []
      for (let y = 0; y < actualRows.value; y++) {
        for (let x = oldCols; x < actualCols.value; x++) {
          rightNewCells.push({
            x,
            y,
            type: 'empty',
            zoneId: undefined,
            shelfConfig: undefined
          })
        }
      }
      // 按正确顺序重新组织
      const mergedCellsRight: CanvasCell[] = []
      for (let y = 0; y < actualRows.value; y++) {
        for (let x = 0; x < actualCols.value; x++) {
          if (x < oldCols) {
            const existingCell = cells.value.find(c => c.x === x && c.y === y)
            if (existingCell) {
              mergedCellsRight.push(existingCell)
            }
          } else {
            const newCell = rightNewCells.find(c => c.x === x && c.y === y)
            if (newCell) {
              mergedCellsRight.push(newCell)
            }
          }
        }
      }
      cells.value = mergedCellsRight
      break
  }
  
  // 清除选中状态
  selectedCell.value = null
}

// 检查是否可以收缩
const canShrink = (direction: 'top' | 'bottom' | 'left' | 'right'): boolean => {
  const minSize = 5 // 最小尺寸
  
  switch (direction) {
    case 'top':
    case 'bottom':
      if (actualRows.value <= minSize) return false
      break
    case 'left':
    case 'right':
      if (actualCols.value <= minSize) return false
      break
  }
  
  // 检查要删除的行/列是否有内容
  switch (direction) {
    case 'top':
      // 检查第一行是否有内容
      return !cells.value.some(c => c.y === 0 && c.type !== 'empty')
    case 'bottom':
      // 检查最后一行是否有内容
      return !cells.value.some(c => c.y === actualRows.value - 1 && c.type !== 'empty')
    case 'left':
      // 检查第一列是否有内容
      return !cells.value.some(c => c.x === 0 && c.type !== 'empty')
    case 'right':
      // 检查最后一列是否有内容
      return !cells.value.some(c => c.x === actualCols.value - 1 && c.type !== 'empty')
  }
  return true
}

// 收缩画布（不影响工具栏的网格大小设置）
const shrinkCanvas = (direction: 'top' | 'bottom' | 'left' | 'right') => {
  if (!canShrink(direction)) {
    ElMessage.warning('该边缘有内容，无法收缩。请先清除边缘内容。')
    return
  }
  
  hasUnsavedChanges.value = true
  
  switch (direction) {
    case 'top':
      // 从顶部收缩：删除第一行，所有元素 y 坐标 -1
      actualRows.value -= 1
      // 删除第一行的单元格
      cells.value = cells.value.filter(c => c.y !== 0)
      // 所有剩余单元格 y 坐标 -1
      cells.value.forEach(cell => {
        cell.y -= 1
      })
      break
      
    case 'bottom':
      // 从底部收缩：删除最后一行
      actualRows.value -= 1
      cells.value = cells.value.filter(c => c.y < actualRows.value)
      break
      
    case 'left':
      // 从左侧收缩：删除第一列，所有元素 x 坐标 -1
      actualCols.value -= 1
      // 删除第一列的单元格
      cells.value = cells.value.filter(c => c.x !== 0)
      // 所有剩余单元格 x 坐标 -1
      cells.value.forEach(cell => {
        cell.x -= 1
      })
      break
      
    case 'right':
      // 从右侧收缩：删除最后一列
      actualCols.value -= 1
      cells.value = cells.value.filter(c => c.x < actualCols.value)
      break
  }
  
  // 清除选中状态
  selectedCell.value = null
}

// 获取单元格
const getCell = (x: number, y: number): CanvasCell | undefined => {
  return cells.value.find(c => c.x === x && c.y === y)
}

// 设置单元格
const setCell = (x: number, y: number, type: CellType) => {
  const cell = getCell(x, y)
  if (!cell) return

  // 只在初始加载完成后才标记修改
  if (!isInitialLoad.value) {
    hasUnsavedChanges.value = true
  }

  if (type === 'empty') {
    cell.type = 'empty'
    cell.zoneId = undefined
    cell.shelfConfig = undefined
  } else if (type === 'shelf') {
    cell.type = 'shelf'
    cell.zoneId = currentZoneId.value
    cell.shelfConfig = { ...shelfConfig }
  } else if (type === 'aisle') {
    cell.type = 'aisle'
    cell.zoneId = currentZoneId.value
    cell.shelfConfig = undefined
  }
}

// 选中单元格
const selectCell = (cell: CanvasCell | null) => {
  selectedCell.value = cell
  if (cell && cell.type === 'shelf' && cell.shelfConfig) {
    // 将选中货架的配置同步到属性面板
    shelfConfig.rows = cell.shelfConfig.rows
    shelfConfig.columns = cell.shelfConfig.columns
    shelfConfig.layers = cell.shelfConfig.layers || 1
    shelfConfig.shelfType = cell.shelfConfig.shelfType
  }
}

// 更新选中货架的配置
const updateSelectedShelfConfig = () => {
  if (selectedCell.value && selectedCell.value.type === 'shelf' && selectedCell.value.shelfConfig) {
    selectedCell.value.shelfConfig.rows = shelfConfig.rows
    selectedCell.value.shelfConfig.columns = shelfConfig.columns
    selectedCell.value.shelfConfig.layers = shelfConfig.layers
    selectedCell.value.shelfConfig.shelfType = shelfConfig.shelfType
  }
  // 保存当前配置作为默认值
  saveShelfConfig()
}

// 开始绘制
const startDraw = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.classList.contains('grid-cell')) return
  
  const x = Number(target.dataset.x)
  const y = Number(target.dataset.y)
  const cell = getCell(x, y)
  
  // 如果点击的是已有的货架，选中它并显示属性
  if (cell && cell.type === 'shelf') {
    selectCell(cell)
    // 如果当前工具是橡皮擦，则擦除
    if (currentTool.value === 'eraser') {
      isDrawing.value = true
      setCell(x, y, 'empty')
      selectCell(null)
    }
    return
  }
  
  // 否则开始绘制
  isDrawing.value = true
  selectCell(null)
  
  if (currentTool.value === 'eraser') {
    setCell(x, y, 'empty')
  } else {
    setCell(x, y, currentTool.value)
  }
}

// 继续绘制
const continueDraw = (e: MouseEvent) => {
  if (!isDrawing.value) return
  
  const target = e.target as HTMLElement
  if (!target.classList.contains('grid-cell')) return
  
  const x = Number(target.dataset.x)
  const y = Number(target.dataset.y)
  
  if (currentTool.value === 'eraser') {
    setCell(x, y, 'empty')
  } else {
    setCell(x, y, currentTool.value)
  }
}

// 停止绘制
const stopDraw = () => {
  isDrawing.value = false
}

// ==================== 框选和拖拽相关 ====================

// 单元格大小常量
const CELL_SIZE = 28
const CELL_GAP = 2
const CELL_TOTAL = CELL_SIZE + CELL_GAP

// 像素坐标转网格坐标
const pixelToGrid = (px: number, py: number) => {
  return {
    x: Math.floor(px / CELL_TOTAL),
    y: Math.floor(py / CELL_TOTAL)
  }
}

// 网格坐标转像素坐标
const gridToPixel = (gx: number, gy: number) => {
  return {
    x: gx * CELL_TOTAL,
    y: gy * CELL_TOTAL
  }
}

// 框选矩形样式
const selectionBoxStyle = computed(() => {
  const left = Math.min(selectionStart.value.x, selectionEnd.value.x)
  const top = Math.min(selectionStart.value.y, selectionEnd.value.y)
  const width = Math.abs(selectionEnd.value.x - selectionStart.value.x)
  const height = Math.abs(selectionEnd.value.y - selectionStart.value.y)
  
  return {
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
    height: `${height}px`
  }
})

// 拖拽预览单元格
const dragPreviewCells = computed(() => {
  if (!isDraggingSelection.value || selectedCells.value.length === 0) return []
  
  const offsetX = dragCurrentGrid.value.x - dragStartGrid.value.x
  const offsetY = dragCurrentGrid.value.y - dragStartGrid.value.y
  
  return selectedCells.value.map(cell => ({
    x: cell.x + offsetX,
    y: cell.y + offsetY,
    type: cell.type,
    zoneId: cell.zoneId
  }))
})

// 粘贴预览单元格
const pastePreviewCells = computed(() => {
  if (!pastePreviewPos.value || clipboard.value.length === 0) return []
  
  const offsetX = pastePreviewPos.value.x - clipboardOffset.value.x
  const offsetY = pastePreviewPos.value.y - clipboardOffset.value.y
  
  return clipboard.value.map(cell => ({
    x: cell.x + offsetX,
    y: cell.y + offsetY,
    type: cell.type,
    zoneId: cell.zoneId
  }))
})

// 获取拖拽预览样式
const getDragPreviewStyle = (preview: { x: number, y: number, zoneId?: string }) => {
  const zone = zones.value.find(z => z.id === preview.zoneId)
  const color = zone?.color || '#409eff'
  return {
    left: `${preview.x * CELL_TOTAL + 2}px`,
    top: `${preview.y * CELL_TOTAL + 2}px`,
    width: `${CELL_SIZE}px`,
    height: `${CELL_SIZE}px`,
    backgroundColor: color
  }
}

// 获取粘贴预览样式
const getPastePreviewStyle = (preview: { x: number, y: number, zoneId?: string }) => {
  const zone = zones.value.find(z => z.id === preview.zoneId)
  const color = zone?.color || '#409eff'
  return {
    left: `${preview.x * CELL_TOTAL + 2}px`,
    top: `${preview.y * CELL_TOTAL + 2}px`,
    width: `${CELL_SIZE}px`,
    height: `${CELL_SIZE}px`,
    backgroundColor: color
  }
}

// 检查点击是否在已选中区域内
const isClickInSelectedArea = (x: number, y: number): boolean => {
  return selectedCells.value.some(cell => cell.x === x && cell.y === y)
}

// 清除多选
const clearMultiSelection = () => {
  selectedCells.value = []
  pastePreviewPos.value = null
}

// 统一的鼠标按下事件处理
const handleCanvasMouseDown = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  const rect = canvasGridRef.value?.getBoundingClientRect()
  if (!rect) return
  
  const relativeX = e.clientX - rect.left
  const relativeY = e.clientY - rect.top
  const gridPos = pixelToGrid(relativeX, relativeY)
  
  // 选择工具模式
  if (currentTool.value === 'select') {
    // 检查是否点击在已选中区域内（开始拖拽移动）
    if (isClickInSelectedArea(gridPos.x, gridPos.y)) {
      isDraggingSelection.value = true
      dragStartGrid.value = { x: gridPos.x, y: gridPos.y }
      dragCurrentGrid.value = { x: gridPos.x, y: gridPos.y }
      return
    }
    
    // 否则开始框选
    clearMultiSelection()
    isSelecting.value = true
    selectionStart.value = { x: relativeX, y: relativeY }
    selectionEnd.value = { x: relativeX, y: relativeY }
    return
  }
  
  // 其他工具（货架、通道、橡皮擦）- 调用原有的绘制逻辑
  startDraw(e)
}

// 统一的鼠标移动事件处理
const handleCanvasMouseMove = (e: MouseEvent) => {
  const rect = canvasGridRef.value?.getBoundingClientRect()
  if (!rect) return
  
  const relativeX = e.clientX - rect.left
  const relativeY = e.clientY - rect.top
  const gridPos = pixelToGrid(relativeX, relativeY)
  
  // 框选中
  if (isSelecting.value) {
    selectionEnd.value = { x: relativeX, y: relativeY }
    return
  }
  
  // 拖拽移动中
  if (isDraggingSelection.value) {
    dragCurrentGrid.value = { x: gridPos.x, y: gridPos.y }
    return
  }
  
  // 如果有剪贴板内容，更新粘贴预览位置
  if (currentTool.value === 'select' && clipboard.value.length > 0) {
    pastePreviewPos.value = { x: gridPos.x, y: gridPos.y }
  }
  
  // 其他工具的绘制逻辑
  if (currentTool.value !== 'select') {
    continueDraw(e)
  }
}

// 统一的鼠标释放事件处理
const handleCanvasMouseUp = (e: MouseEvent) => {
  // 完成框选
  if (isSelecting.value) {
    finishSelection()
    isSelecting.value = false
    return
  }
  
  // 完成拖拽移动
  if (isDraggingSelection.value) {
    finishDragMove()
    isDraggingSelection.value = false
    return
  }
  
  // 其他工具
  if (currentTool.value !== 'select') {
    stopDraw()
  }
}

// 鼠标离开画布
const handleCanvasMouseLeave = () => {
  if (isSelecting.value) {
    finishSelection()
    isSelecting.value = false
  }
  if (isDraggingSelection.value) {
    // 取消拖拽，不执行移动
    isDraggingSelection.value = false
  }
  if (currentTool.value !== 'select') {
    stopDraw()
  }
}

// 完成框选，计算选中的单元格
const finishSelection = () => {
  const startGrid = pixelToGrid(
    Math.min(selectionStart.value.x, selectionEnd.value.x),
    Math.min(selectionStart.value.y, selectionEnd.value.y)
  )
  const endGrid = pixelToGrid(
    Math.max(selectionStart.value.x, selectionEnd.value.x),
    Math.max(selectionStart.value.y, selectionEnd.value.y)
  )
  
  // 找出框选范围内的所有非空单元格
  const selected: CanvasCell[] = []
  for (let y = startGrid.y; y <= endGrid.y; y++) {
    for (let x = startGrid.x; x <= endGrid.x; x++) {
      const cell = getCell(x, y)
      if (cell && cell.type !== 'empty') {
        selected.push(cell)
      }
    }
  }
  
  selectedCells.value = selected
  
  // 清除单选
  selectedCell.value = null
}

// 完成拖拽移动
const finishDragMove = () => {
  if (selectedCells.value.length === 0) return
  
  const offsetX = dragCurrentGrid.value.x - dragStartGrid.value.x
  const offsetY = dragCurrentGrid.value.y - dragStartGrid.value.y
  
  // 如果没有移动，不做任何操作
  if (offsetX === 0 && offsetY === 0) return
  
  // 检查目标位置是否有效
  const canMove = selectedCells.value.every(cell => {
    const newX = cell.x + offsetX
    const newY = cell.y + offsetY
    // 检查是否在画布范围内
    if (newX < 0 || newX >= actualCols.value || newY < 0 || newY >= actualRows.value) {
      return false
    }
    // 检查目标位置是否为空或是选中区域的一部分
    const targetCell = getCell(newX, newY)
    if (!targetCell) return false
    if (targetCell.type !== 'empty') {
      // 如果目标位置不为空，检查是否是选中区域的一部分
      return selectedCells.value.some(c => c.x === newX && c.y === newY)
    }
    return true
  })
  
  if (!canMove) {
    ElMessage.warning('目标位置无效或超出画布范围')
    return
  }
  
  hasUnsavedChanges.value = true
  
  // 保存要移动的单元格数据（深拷贝）
  const cellsToMove = selectedCells.value.map(cell => ({
    x: cell.x,
    y: cell.y,
    type: cell.type,
    zoneId: cell.zoneId,
    shelfConfig: cell.shelfConfig ? { ...cell.shelfConfig } : undefined
  }))
  
  // 先清空原位置
  cellsToMove.forEach(cellData => {
    const cell = getCell(cellData.x, cellData.y)
    if (cell) {
      cell.type = 'empty'
      cell.zoneId = undefined
      cell.shelfConfig = undefined
    }
  })
  
  // 再填充新位置
  cellsToMove.forEach(cellData => {
    const newX = cellData.x + offsetX
    const newY = cellData.y + offsetY
    const cell = getCell(newX, newY)
    if (cell) {
      cell.type = cellData.type
      cell.zoneId = cellData.zoneId  // 保持原库区
      cell.shelfConfig = cellData.shelfConfig
    }
  })
  
  // 更新选中区域的坐标
  selectedCells.value = cellsToMove.map(cellData => {
    const newX = cellData.x + offsetX
    const newY = cellData.y + offsetY
    return getCell(newX, newY)!
  }).filter(Boolean)
  
  ElMessage.success('移动成功')
}

// ==================== 键盘快捷键 ====================

// 复制选中的单元格
const copySelectedCells = () => {
  if (selectedCells.value.length === 0) {
    ElMessage.warning('请先选择要复制的单元格')
    return
  }
  
  // 深拷贝选中的单元格
  clipboard.value = selectedCells.value.map(cell => ({
    x: cell.x,
    y: cell.y,
    type: cell.type,
    zoneId: cell.zoneId,
    shelfConfig: cell.shelfConfig ? { ...cell.shelfConfig } : undefined
  }))
  
  // 计算选中区域的最小坐标作为基准偏移
  const minX = Math.min(...selectedCells.value.map(c => c.x))
  const minY = Math.min(...selectedCells.value.map(c => c.y))
  clipboardOffset.value = { x: minX, y: minY }
  
  isCut.value = false
  ElMessage.success(`已复制 ${clipboard.value.length} 个单元格`)
}

// 剪切选中的单元格
const cutSelectedCells = () => {
  if (selectedCells.value.length === 0) {
    ElMessage.warning('请先选择要剪切的单元格')
    return
  }
  
  // 先复制
  copySelectedCells()
  isCut.value = true
  ElMessage.success(`已剪切 ${clipboard.value.length} 个单元格`)
}

// 粘贴单元格
const pasteCells = () => {
  if (clipboard.value.length === 0) {
    ElMessage.warning('剪贴板为空')
    return
  }
  
  if (!pastePreviewPos.value) {
    ElMessage.warning('请将鼠标移动到目标位置')
    return
  }
  
  const offsetX = pastePreviewPos.value.x - clipboardOffset.value.x
  const offsetY = pastePreviewPos.value.y - clipboardOffset.value.y
  
  // 检查目标位置是否有效
  const canPaste = clipboard.value.every(cellData => {
    const newX = cellData.x + offsetX
    const newY = cellData.y + offsetY
    // 检查是否在画布范围内
    if (newX < 0 || newX >= actualCols.value || newY < 0 || newY >= actualRows.value) {
      return false
    }
    // 检查目标位置是否为空
    const targetCell = getCell(newX, newY)
    return targetCell && targetCell.type === 'empty'
  })
  
  if (!canPaste) {
    ElMessage.warning('目标位置无效或已有内容')
    return
  }
  
  hasUnsavedChanges.value = true
  
  // 如果是剪切操作，先清空原位置
  if (isCut.value) {
    clipboard.value.forEach(cellData => {
      const cell = getCell(cellData.x, cellData.y)
      if (cell) {
        cell.type = 'empty'
        cell.zoneId = undefined
        cell.shelfConfig = undefined
      }
    })
  }
  
  // 粘贴到新位置
  const newSelectedCells: CanvasCell[] = []
  clipboard.value.forEach(cellData => {
    const newX = cellData.x + offsetX
    const newY = cellData.y + offsetY
    const cell = getCell(newX, newY)
    if (cell) {
      cell.type = cellData.type
      cell.zoneId = cellData.zoneId  // 保持原库区
      cell.shelfConfig = cellData.shelfConfig ? { ...cellData.shelfConfig } : undefined
      newSelectedCells.push(cell)
    }
  })
  
  // 更新选中区域为粘贴后的单元格
  selectedCells.value = newSelectedCells
  
  // 如果是剪切，清空剪贴板
  if (isCut.value) {
    clipboard.value = []
    isCut.value = false
  }
  
  // 清除粘贴预览
  pastePreviewPos.value = null
  
  ElMessage.success('粘贴成功')
}

// 删除选中的单元格
const deleteSelectedCells = () => {
  if (selectedCells.value.length === 0) return
  
  hasUnsavedChanges.value = true
  
  selectedCells.value.forEach(cell => {
    cell.type = 'empty'
    cell.zoneId = undefined
    cell.shelfConfig = undefined
  })
  
  ElMessage.success(`已删除 ${selectedCells.value.length} 个单元格`)
  clearMultiSelection()
}

// 键盘事件处理
const handleKeyDown = (e: KeyboardEvent) => {
  // Ctrl+C: 复制
  if (e.ctrlKey && e.key === 'c') {
    e.preventDefault()
    copySelectedCells()
    return
  }
  
  // Ctrl+X: 剪切
  if (e.ctrlKey && e.key === 'x') {
    e.preventDefault()
    cutSelectedCells()
    return
  }
  
  // Ctrl+V: 粘贴
  if (e.ctrlKey && e.key === 'v') {
    e.preventDefault()
    pasteCells()
    return
  }
  
  // Delete/Backspace: 删除
  if (e.key === 'Delete' || e.key === 'Backspace') {
    // 只在选择工具模式下响应删除键
    if (currentTool.value === 'select' && selectedCells.value.length > 0) {
      e.preventDefault()
      deleteSelectedCells()
    }
    return
  }
  
  // Escape: 取消选择
  if (e.key === 'Escape') {
    clearMultiSelection()
    clipboard.value = []
    pastePreviewPos.value = null
    return
  }
}

// 获取单元格样式类
const getCellClass = (cell: CanvasCell) => {
  const isMultiSelected = selectedCells.value.some(c => c.x === cell.x && c.y === cell.y)
  return {
    'cell-shelf': cell.type === 'shelf',
    'cell-aisle': cell.type === 'aisle',
    'cell-empty': cell.type === 'empty',
    'cell-selected': selectedCell.value && selectedCell.value.x === cell.x && selectedCell.value.y === cell.y,
    'cell-multi-selected': isMultiSelected
  }
}

// 获取单元格样式
const getCellStyle = (cell: CanvasCell) => {
  if (cell.type === 'shelf' && cell.zoneId) {
    const zone = zones.value.find(z => z.id === cell.zoneId)
    if (zone) {
      return { backgroundColor: zone.color }
    }
  }
  return {}
}

// 网格样式（使用实际大小）
const gridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${actualCols.value}, 28px)`,
  gridTemplateRows: `repeat(${actualRows.value}, 28px)`
}))

// 当前库区名称
const currentZoneName = computed(() => {
  const zone = zones.value[currentZoneIndex.value]
  return zone?.name || currentZone.value
})

// 当前库区颜色
const currentZoneColor = computed(() => {
  const zone = zones.value[currentZoneIndex.value]
  return zone?.color || '#409eff'
})

// 根据ID获取库区名称
const getZoneNameById = (zoneId?: string) => {
  if (!zoneId) return '-'
  const zone = zones.value.find(z => z.id === zoneId)
  return zone?.name || '-'
}

// 获取货架单元格标签（根据货架类型显示不同标识）
const getShelfLabel = (cell: CanvasCell) => {
  const shelfType = cell.shelfConfig?.shelfType || 'normal'
  switch (shelfType) {
    case 'high_rack': return 'H'  // 高位货架
    case 'ground_stack': return 'G'  // 地堆
    default: return 'S'  // 普通货架
  }
}

// 从图例选择货架类型
const selectShelfType = (type: ShelfType) => {
  currentTool.value = 'shelf'
  shelfConfig.shelfType = type
}

// 从图例选择通道工具
const selectAisleTool = () => {
  currentTool.value = 'aisle'
}

// 显示的单元格（根据是否显示全部库区过滤）
const displayCells = computed(() => {
  if (showAllZones.value) {
    // 显示全部库区
    return cells.value
  }
  // 只显示当前选中库区的单元格，空白格也显示
  return cells.value.map(cell => {
    // 如果是空白格，显示
    if (cell.type === 'empty') {
      return cell
    }
    // 如果属于当前库区，显示（使用唯一ID比较）
    if (cell.zoneId === currentZoneId.value) {
      return cell
    }
    // 其他库区的格子显示为空白（但不修改原数据）
    return {
      ...cell,
      type: 'empty' as CellType,
      _originalType: cell.type,
      _hidden: true
    }
  })
})

// 选择库区（通过索引）
const selectZone = (index: number) => {
  currentZoneIndex.value = index
  // 切换库区时清除选中状态
  selectedCell.value = null
}

// 监听货架配置变化，同步更新选中的货架
watch(shelfConfig, () => {
  updateSelectedShelfConfig()
}, { deep: true })

// 监听库区名称变化，同步更新code
watch(zones, (newZones) => {
  // 只在初始加载完成后才处理
  if (!isInitialLoad.value) {
    hasUnsavedChanges.value = true
    // 根据库区名称自动更新code
    newZones.forEach(zone => {
      const extractedCode = zone.name.match(/^([A-Za-z]+)/)?.[1]?.toUpperCase()
      if (extractedCode && extractedCode !== zone.code) {
        zone.code = extractedCode
      }
    })
  }
}, { deep: true })

// 统计数据（根据显示模式计算当前库区或全部）
const shelfCount = computed(() => {
  const targetCells = showAllZones.value 
    ? cells.value 
    : cells.value.filter(c => c.zoneId === currentZoneId.value)
  return targetCells.filter(c => c.type === 'shelf').length
})
const aisleCount = computed(() => {
  const targetCells = showAllZones.value 
    ? cells.value 
    : cells.value.filter(c => c.zoneId === currentZoneId.value)
  return targetCells.filter(c => c.type === 'aisle').length
})
const estimatedLocations = computed(() => {
  const targetCells = showAllZones.value 
    ? cells.value 
    : cells.value.filter(c => c.zoneId === currentZoneId.value)
  return targetCells
    .filter(c => c.type === 'shelf' && c.shelfConfig)
    .reduce((sum, c) => sum + (c.shelfConfig!.rows * c.shelfConfig!.columns * (c.shelfConfig!.layers || 1)), 0)
})

// 添加库区
const addZone = () => {
  const nextCode = String.fromCharCode(65 + zones.value.length)
  const color = zoneColors[zones.value.length % zoneColors.length]
  zones.value.push({
    id: generateZoneId(),
    code: nextCode,
    name: `${nextCode}库区`,
    color
  })
  // 选中新添加的库区
  currentZoneIndex.value = zones.value.length - 1
  // 标记有未保存的修改
  hasUnsavedChanges.value = true
}

// 删除库区（通过索引）
const removeZone = (index: number) => {
  if (index < 0 || index >= zones.value.length) return
  
  const zoneToRemove = zones.value[index]
  zones.value.splice(index, 1)
  
  // 清除该库区的单元格（使用唯一ID）
  cells.value.forEach(cell => {
    if (cell.zoneId === zoneToRemove.id) {
      cell.type = 'empty'
      cell.zoneId = undefined
      cell.shelfConfig = undefined
    }
  })
  
  // 调整选中索引
  if (currentZoneIndex.value >= zones.value.length) {
    currentZoneIndex.value = Math.max(0, zones.value.length - 1)
  } else if (currentZoneIndex.value > index) {
    currentZoneIndex.value--
  }
  
  // 标记有未保存的修改
  hasUnsavedChanges.value = true
}

// 清空画布
const clearCanvas = async () => {
  await ElMessageBox.confirm('确定要清空画布吗？', '提示', { type: 'warning' })
  initGrid()
  // 标记有未保存的修改
  hasUnsavedChanges.value = true
}

// 生成布局配置
const generateLayoutConfig = () => {
  const zonesConfig: any[] = []
  
  // 按库区分组（使用唯一ID）
  zones.value.forEach(zone => {
    const zoneCells = cells.value.filter(
      c => c.zoneId === zone.id && (c.type === 'shelf' || c.type === 'aisle')
    )
    
    if (zoneCells.length === 0) return
    
    // 找出所有巷道（连续的通道行）
    const aisleCells = zoneCells.filter(c => c.type === 'aisle')
    const shelfCells = zoneCells.filter(c => c.type === 'shelf')
    
    // 按 Y 坐标分组找出巷道
    const aisleRows = new Set(aisleCells.map(c => c.y))
    
    // 生成巷道配置
    const aisles: any[] = []
    let aisleIdx = 0
    
    // 将货架按 Y 坐标分组
    const shelfRowGroups = new Map<number, CanvasCell[]>()
    shelfCells.forEach(cell => {
      if (!shelfRowGroups.has(cell.y)) {
        shelfRowGroups.set(cell.y, [])
      }
      shelfRowGroups.get(cell.y)!.push(cell)
    })
    
    // 为每行货架创建巷道
    const sortedRows = Array.from(shelfRowGroups.keys()).sort((a, b) => a - b)
    
    sortedRows.forEach((rowY, idx) => {
      const rowCells = shelfRowGroups.get(rowY)!.sort((a, b) => a.x - b.x)
      
      const aisleCode = `${String(idx + 1).padStart(2, '0')}巷`
      const shelves: any[] = []
      
      // 将连续的货架合并为一个货架单元
      // 根据货架类型生成不同的名称前缀
      const getShelfTypePrefix = (type: string) => {
        switch (type) {
          case 'high_rack': return '高架'
          case 'ground_stack': return '地堆'
          default: return '货架'
        }
      }
      
      let shelfIdx = 0
      rowCells.forEach(cell => {
        shelfIdx++
        const shelfType = cell.shelfConfig?.shelfType || 'normal'
        const typePrefix = getShelfTypePrefix(shelfType)
        const shelfNum = String(shelfIdx).padStart(2, '0')
        shelves.push({
          code: `${typePrefix}${shelfNum}`,
          name: `${typePrefix}${shelfNum}`,
          shelf_type: shelfType,
          rows: cell.shelfConfig?.rows || 4,
          columns: cell.shelfConfig?.columns || 5,
          layers: cell.shelfConfig?.layers || 1,
          x_coordinate: cell.x
        })
      })
      
      if (shelves.length > 0) {
        aisles.push({
          code: aisleCode,
          name: aisleCode,
          y_coordinate: rowY,
          shelves
        })
      }
    })
    
    if (aisles.length > 0) {
      // 从库区名称中提取代码（如"C库区"提取"C"，"B库区"提取"B"）
      const extractedCode = zone.name.match(/^([A-Za-z]+)/)?.[1]?.toUpperCase() || zone.code
      zonesConfig.push({
        code: extractedCode,
        name: zone.name,
        aisles
      })
    }
  })
  
  return zonesConfig
}

// 保存布局
const saveLayout = async () => {
  if (!warehouse.value) return
  
  const zonesConfig = generateLayoutConfig()
  
  if (zonesConfig.length === 0) {
    ElMessage.warning('请先在画布上绘制布局')
    return
  }
  
  const totalLocations = estimatedLocations.value
  
  await ElMessageBox.confirm(
    `确定要保存布局吗？将生成 ${totalLocations} 个库位。`,
    '确认保存',
    { type: 'warning' }
  )
  
  saving.value = true
  try {
    await warehouseApi.setupWarehouseLayout(
      warehouse.value.code,
      warehouse.value.name,
      zonesConfig
    )
    // 标记已保存
    hasUnsavedChanges.value = false
    ElMessage.success('布局保存成功')
    router.push('/warehouse')
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '保存失败'
    ElMessage.error(errorMsg)
  } finally {
    saving.value = false
  }
}

// 返回
const goBack = async () => {
  if (hasUnsavedChanges.value) {
    try {
      await ElMessageBox.confirm(
        '您有未保存的修改，确定要离开吗？',
        '未保存的修改',
        { 
          type: 'warning',
          confirmButtonText: '离开',
          cancelButtonText: '取消'
        }
      )
      hasUnsavedChanges.value = false  // 防止路由守卫再次提示
      router.push('/warehouse')
    } catch {
      // 用户取消
    }
  } else {
    router.push('/warehouse')
  }
}

// 加载仓库信息
const loadWarehouse = async () => {
  try {
    warehouse.value = await warehouseApi.getWarehouse(warehouseId.value)
  } catch (error) {
    ElMessage.error('加载仓库信息失败')
    router.push('/warehouse')
  }
}

// 加载现有布局
const loadExistingLayout = async () => {
  try {
    const layoutData = await warehouseApi.getWarehouseLayout(warehouseId.value)
    
    if (!layoutData.zones || layoutData.zones.length === 0) {
      // 没有现有布局，使用空白画布
      return
    }
    
    // 恢复库区列表，为每个库区生成唯一ID
    // 同时建立 code -> id 的映射关系
    const zoneIdMap = new Map<string, string>()
    zones.value = layoutData.zones.map((z: any, index: number) => {
      const uniqueId = `zone_load_${index}_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`
      zoneIdMap.set(z.code, uniqueId)
      return {
        id: uniqueId,
        code: z.code,
        name: z.name,
        color: z.color
      }
    })
    // 选中第一个库区
    currentZoneIndex.value = 0
    
    // 计算需要的网格大小
    let maxX = 0
    let maxY = 0
    
    layoutData.zones.forEach((zone: any) => {
      zone.aisles?.forEach((aisle: any) => {
        if (aisle.y_coordinate > maxY) {
          maxY = aisle.y_coordinate
        }
        aisle.shelves?.forEach((shelf: any) => {
          if (shelf.x_coordinate > maxX) {
            maxX = shelf.x_coordinate
          }
        })
      })
    })
    
    // 确保网格足够大（至少留5格边距）
    if (maxX + 5 > gridCols.value) {
      gridCols.value = maxX + 5
    }
    if (maxY + 5 > gridRows.value) {
      gridRows.value = maxY + 5
    }
    
    // 同步实际大小
    actualCols.value = gridCols.value
    actualRows.value = gridRows.value
    
    // 重新初始化网格
    initGrid()
    
    // 将布局数据填充到画布
    let firstShelfCell: CanvasCell | null = null
    
    // 为每个库区分配唯一的zoneId
    layoutData.zones.forEach((zone: any, zoneIndex: number) => {
      const zoneId = zones.value[zoneIndex]?.id
      if (!zoneId) return
      
      zone.aisles?.forEach((aisle: any) => {
        const y = aisle.y_coordinate
        
        aisle.shelves?.forEach((shelf: any) => {
          const x = shelf.x_coordinate
          const cell = getCell(x, y)
          
          if (cell) {
            cell.type = 'shelf'
            cell.zoneId = zoneId  // 使用唯一ID
            cell.shelfConfig = {
              rows: shelf.rows,
              columns: shelf.columns,
              layers: shelf.layers || 1,
              shelfType: shelf.shelf_type as ShelfType
            }
            
            // 记录第一个货架
            if (!firstShelfCell) {
              firstShelfCell = cell
            }
          }
        })
      })
    })
    
    // 自动选中第一个货架，让属性面板显示其配置
    if (firstShelfCell) {
      selectCell(firstShelfCell)
    }
    
    ElMessage.success('已加载现有布局，可继续编辑')
  } catch (error) {
    console.error('加载布局失败:', error)
    // 加载失败不影响使用，继续使用空白画布
  }
}

// 初始化
onMounted(async () => {
  await loadWarehouse()
  initGrid()
  await loadExistingLayout()
  
  // 初始加载完成，重置状态
  isInitialLoad.value = false
  hasUnsavedChanges.value = false
  
  // 添加浏览器关闭/刷新提示
  window.addEventListener('beforeunload', handleBeforeUnload)
  
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeyDown)
})

// 清理
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('keydown', handleKeyDown)
})

// 浏览器关闭/刷新时的提示
const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (hasUnsavedChanges.value) {
    e.preventDefault()
    e.returnValue = '您有未保存的修改，确定要离开吗？'
    return e.returnValue
  }
}

// 路由离开守卫
onBeforeRouteLeave(async (to, from, next) => {
  if (hasUnsavedChanges.value) {
    try {
      await ElMessageBox.confirm(
        '您有未保存的修改，确定要离开吗？',
        '未保存的修改',
        { 
          type: 'warning',
          confirmButtonText: '离开',
          cancelButtonText: '取消'
        }
      )
      next()
    } catch {
      next(false)
    }
  } else {
    next()
  }
})
</script>

<style lang="scss" scoped>
.canvas-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  
  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .warehouse-name {
      font-size: 16px;
      font-weight: 500;
      color: #303133;
    }
  }
  
  .toolbar-center {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .grid-size-label {
      font-size: 14px;
      color: #606266;
    }
  }
  
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .unsaved-tag {
      animation: pulse 1.5s ease-in-out infinite;
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}

.left-panel, .right-panel {
  width: 220px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.panel-card {
  :deep(.el-card__header) {
    padding: 12px 16px;
    font-weight: 500;
  }
  
  :deep(.el-card__body) {
    padding: 16px;
  }
  
  .info-icon {
    margin-left: 8px;
    color: #909399;
    cursor: help;
    
    &:hover {
      color: #409eff;
    }
  }
}

.shelf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.zone-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.zone-filter {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #eee;
}

.zone-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.zone-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
  
  &:hover {
    background: #f5f7fa;
  }
  
  &.active {
    background: #ecf5ff;
    border-color: #409eff;
    
    .zone-color {
      transform: scale(1.1);
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
    }
  }
  
  .zone-color {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    transition: all 0.2s;
  }
}

.legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  
  &.clickable {
    cursor: pointer;
    padding: 4px 8px;
    margin: -4px -8px;
    border-radius: 4px;
    transition: all 0.2s;
    
    &:hover {
      background: #f5f7fa;
    }
    
    &.active {
      background: #ecf5ff;
      color: #409eff;
      font-weight: 500;
      
      .legend-color {
        box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
      }
    }
  }
  
  .legend-color {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #ddd;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: bold;
    color: #fff;
    
    &.shelf {
      background: #409eff;
    }
    
    &.aisle {
      background: #909399;
    }
    
    &.empty {
      background: #fff;
    }
  }
}

.canvas-container {
  flex: 1;
  overflow: auto;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.canvas-wrapper {
  display: grid;
  grid-template-areas:
    ".    top    ."
    "left canvas right"
    ".    bottom .";
  grid-template-columns: auto 1fr auto;
  grid-template-rows: auto 1fr auto;
  gap: 8px;
  align-items: center;
  justify-items: center;
}

.btn-group {
  display: flex;
  gap: 4px;
  
  &.btn-group-top {
    grid-area: top;
    flex-direction: row;
  }
  
  &.btn-group-bottom {
    grid-area: bottom;
    flex-direction: row;
  }
  
  &.btn-group-left {
    grid-area: left;
    flex-direction: column;
  }
  
  &.btn-group-right {
    grid-area: right;
    flex-direction: column;
  }
}

.expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #f5f7fa;
  border: 2px dashed #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  color: #909399;
  transition: all 0.2s ease;
  
  &:hover:not(.disabled) {
    background: #ecf5ff;
    border-color: #409eff;
    color: #409eff;
    transform: scale(1.1);
  }
  
  &:active:not(.disabled) {
    transform: scale(0.95);
  }
  
  &.disabled {
    opacity: 0.4;
    cursor: not-allowed;
    
    &:hover {
      transform: none;
    }
  }
  
  .el-icon {
    font-size: 14px;
  }
}

.canvas-grid {
  grid-area: canvas;
}

.canvas-zone-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 14px;
  color: #606266;
  
  .zone-indicator-color {
    width: 14px;
    height: 14px;
    border-radius: 3px;
  }
}

.canvas-grid {
  display: grid;
  gap: 2px;
  background: #eee;
  padding: 2px;
  border-radius: 4px;
  user-select: none;
  position: relative;  // 用于定位框选矩形和预览单元格
}

.grid-cell {
  width: 28px;
  height: 28px;
  background: #fff;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  position: relative;  // 用于定位多选高亮伪元素
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }
  
  &.cell-shelf {
    background: #409eff;
    color: #fff;
  }
  
  &.cell-aisle {
    background: #909399;
    color: #fff;
  }
  
  &.cell-empty {
    background: #fff;
  }
  
  &.cell-selected {
    outline: 3px solid #e6a23c;
    outline-offset: -1px;
    z-index: 10;
  }
  
  &.cell-multi-selected {
    outline: 2px solid #67c23a;
    outline-offset: -1px;
    z-index: 5;
    
    &::after {
      content: '';
      position: absolute;
      inset: 0;
      background: rgba(103, 194, 58, 0.2);
      pointer-events: none;
    }
  }
  
  .cell-label {
    font-size: 10px;
    font-weight: bold;
  }
}

// 框选矩形
.selection-box {
  position: absolute;
  background: rgba(64, 158, 255, 0.2);
  border: 2px dashed #409eff;
  pointer-events: none;
  z-index: 100;
}

// 拖拽预览单元格
.drag-preview-cell {
  position: absolute;
  border-radius: 2px;
  opacity: 0.5;
  pointer-events: none;
  z-index: 50;
  border: 2px dashed #67c23a;
}

// 粘贴预览单元格
.paste-preview-cell {
  position: absolute;
  border-radius: 2px;
  opacity: 0.4;
  pointer-events: none;
  z-index: 50;
  border: 2px dashed #e6a23c;
}

.selected-info {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ddd;
  font-size: 12px;
  color: #909399;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .stat-label {
    font-size: 13px;
    color: #909399;
  }
  
  .stat-value {
    font-size: 18px;
    font-weight: 600;
    color: #409eff;
  }
}

.tips {
  font-size: 13px;
  color: #909399;
  line-height: 1.8;
  
  p {
    margin: 0;
  }
}
</style>
