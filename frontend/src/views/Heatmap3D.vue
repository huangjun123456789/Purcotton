<template>
  <div class="heatmap-3d-page">
    <!-- 页面标签 -->
    <div class="page-tabs">
      <el-tag type="info" effect="plain" closable>3D 库位分布</el-tag>
      <div class="view-switch">
        <el-button-group>
          <el-button 
            :type="currentView === 'heatmap' ? 'default' : 'primary'" 
            @click="$router.push('/heatmap')"
          >
            2D 视图
          </el-button>
          <el-button type="primary">
            3D 视图
          </el-button>
        </el-button-group>
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
        <span class="filter-label">高度表示:</span>
        <el-select v-model="heightMode" style="width: 120px" @change="updateScene">
          <el-option label="热度值" value="heat" />
          <el-option label="库存量" value="inventory" />
          <el-option label="固定高度" value="fixed" />
        </el-select>
      </div>

      <div class="filter-actions">
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          查 询
        </el-button>
        <el-button @click="resetCamera">
          <el-icon><Refresh /></el-icon>
          重置视角
        </el-button>
      </div>
    </div>

    <!-- 热力图图例 -->
    <div class="heat-legend card">
      <span class="legend-label">0</span>
      <div class="legend-bar"></div>
      <span class="legend-label">{{ store.HEAT_COLOR_CAP }}+</span>
      <span class="legend-tip">（热度值）</span>
    </div>

    <!-- 3D 场景容器 -->
    <div class="scene-container card" v-loading="loading">
      <div ref="sceneRef" class="three-scene"></div>
      
      <!-- 视角控制 -->
      <div class="view-controls">
        <el-button-group size="small">
          <el-button @click="setView('top')" :type="activeView === 'top' ? 'primary' : 'default'">
            俯视
          </el-button>
          <el-button @click="setView('front')" :type="activeView === 'front' ? 'primary' : 'default'">
            正视
          </el-button>
          <el-button @click="setView('side')" :type="activeView === 'side' ? 'primary' : 'default'">
            侧视
          </el-button>
          <el-button @click="setView('perspective')" :type="activeView === 'perspective' ? 'primary' : 'default'">
            3D
          </el-button>
        </el-button-group>
      </div>

      <!-- 操作提示 -->
      <div class="controls-hint">
        <span>🖱️ 左键拖拽旋转 | 右键平移 | 滚轮缩放 | 点击货架查看详情</span>
      </div>

      <el-empty v-if="!heatmapData && !loading" description="暂无数据" />
    </div>

    <!-- 悬浮提示 -->
    <div 
      class="hover-tooltip" 
      v-show="tooltipVisible"
      :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
    >
      <template v-if="hoverShelf">
        <div><strong>{{ hoverShelf.shelf_name }}</strong></div>
        <div>层数: {{ hoverShelf.layers || 1 }} 层</div>
        <div>热度: {{ hoverShelf.maxHeat?.toFixed(0) || 0 }}</div>
        <div>库位数: {{ hoverShelf.locations?.length || 0 }}</div>
      </template>
    </div>

    <!-- 库位详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="货架详情"
      width="500px"
    >
      <div class="shelf-detail" v-if="selectedShelf">
        <div class="detail-header">
          <h3>{{ selectedShelf.shelf_name }}</h3>
          <el-tag :type="getShelfTypeTag(selectedShelf.shelf_type)">
            {{ getShelfTypeName(selectedShelf.shelf_type) }}
          </el-tag>
        </div>
        <el-divider />
        <div class="detail-stats">
          <div class="stat-item">
            <span class="stat-label">货架层数</span>
            <span class="stat-value highlight">{{ selectedShelf.layers || 1 }} 层</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最大热度</span>
            <span class="stat-value">{{ getShelfMaxHeat(selectedShelf.locations).toFixed(0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">平均热度</span>
            <span class="stat-value">{{ getShelfAvgHeat(selectedShelf.locations).toFixed(0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">库位数量</span>
            <span class="stat-value">{{ selectedShelf.locations?.length || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">总库存</span>
            <span class="stat-value">{{ getTotalInventory(selectedShelf.locations) }}</span>
          </div>
        </div>
        <el-divider />
        <div class="locations-grid" v-if="selectedShelf.locations?.length">
          <div class="grid-title">库位明细</div>
          <div class="location-items">
            <div 
              v-for="loc in selectedShelf.locations" 
              :key="loc.location_id"
              class="location-item"
              :style="{ backgroundColor: getHeatColor(loc.heat_value) }"
            >
              <span class="loc-code">{{ loc.location_code }}</span>
              <span class="loc-heat">{{ loc.heat_value.toFixed(0) }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useHeatmapStore } from '@/stores/heatmap'
import { warehouseApi } from '@/api'
import type { ShelfHeatData, ShelfType, LocationHeatItem } from '@/types'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const store = useHeatmapStore()

// 筛选状态
const selectedWarehouse = ref<number | null>(null)
const selectedZone = ref<number | null>(null)
const heightMode = ref<'heat' | 'inventory' | 'fixed'>('heat')
const warehouses = ref<any[]>([])
const currentView = ref('heatmap3d')
const activeView = ref('perspective')

// 弹窗状态
const detailDialogVisible = ref(false)
const selectedShelf = ref<any>(null)

// 悬浮提示状态
const tooltipVisible = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)
const hoverShelf = ref<any>(null)

// Three.js 引用
const sceneRef = ref<HTMLDivElement | null>(null)
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let raycaster: THREE.Raycaster
let mouse: THREE.Vector2
let shelfMeshes: Map<string, { mesh: THREE.Mesh; data: any }> = new Map()
let animationId: number
let currentLayoutSize = { width: 100, depth: 100 } // 存储当前布局大小

// 从 store 获取数据
const loading = computed(() => store.loading)
const heatmapData = computed(() => store.heatmapData)
const zones = computed(() => store.zones)
const maxHeatValue = computed(() => store.maxHeatValue)
const minHeatValue = computed(() => store.minHeatValue)

// 获取热力颜色
const getHeatColor = (value: number) => store.getHeatColor(value)

// 颜色映射 (热度值 -> THREE.Color)
const getHeatColor3D = (value: number): THREE.Color => {
  const colorStr = store.getHeatColor(value)
  return new THREE.Color(colorStr)
}

// 获取货架最大热力值
const getShelfMaxHeat = (locations: LocationHeatItem[] | undefined): number => {
  if (!locations || locations.length === 0) return 0
  return Math.max(...locations.map(loc => loc.heat_value || 0))
}

// 获取货架平均热力值
const getShelfAvgHeat = (locations: LocationHeatItem[] | undefined): number => {
  if (!locations || locations.length === 0) return 0
  const total = locations.reduce((sum, loc) => sum + (loc.heat_value || 0), 0)
  return total / locations.length
}

// 获取总库存
const getTotalInventory = (locations: LocationHeatItem[] | undefined): number => {
  if (!locations || locations.length === 0) return 0
  return locations.reduce((sum, loc) => sum + (loc.inventory_qty || 0), 0)
}

// 获取货架类型名称
const getShelfTypeName = (type: ShelfType): string => {
  const names: Record<ShelfType, string> = {
    normal: '普通货架',
    high_rack: '高位货架',
    ground_stack: '地堆',
    mezzanine: '阁楼货架',
    cantilever: '悬臂货架'
  }
  return names[type] || '未知'
}

// 获取货架类型标签
const getShelfTypeTag = (type: ShelfType): string => {
  const tags: Record<ShelfType, string> = {
    normal: '',
    high_rack: 'warning',
    ground_stack: 'success',
    mezzanine: 'info',
    cantilever: 'danger'
  }
  return tags[type] || ''
}

// 初始化 Three.js 场景（性能优化版）
const initScene = () => {
  if (!sceneRef.value) return

  const container = sceneRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf0f2f5)

  // 创建相机
  camera = new THREE.PerspectiveCamera(50, width / height, 1, 1000)
  camera.position.set(60, 50, 80)

  // 创建渲染器（性能优化）
  renderer = new THREE.WebGLRenderer({ 
    antialias: false, // 关闭抗锯齿提升性能
    powerPreference: 'high-performance'
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(1) // 固定像素比为1
  renderer.shadowMap.enabled = false // 关闭阴影大幅提升性能
  container.appendChild(renderer.domElement)

  // 创建轨道控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.1
  controls.minDistance = 20
  controls.maxDistance = 500
  controls.maxPolarAngle = Math.PI / 2 - 0.05

  // 简化光照（性能优化）
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5)
  directionalLight.position.set(50, 80, 50)
  scene.add(directionalLight)

  // 地板会在 updateScene 中动态创建

  // 射线检测
  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()

  // 事件监听
  container.addEventListener('mousemove', onMouseMove)
  container.addEventListener('click', onMouseClick)
  window.addEventListener('resize', onWindowResize)

  // 开始渲染循环
  animate()
}

// 清理场景中的所有精灵（标签）和货架组
const clearLabels = () => {
  const objectsToRemove: THREE.Object3D[] = []
  scene.traverse((object) => {
    if (object instanceof THREE.Sprite) {
      objectsToRemove.push(object)
    }
    if (object instanceof THREE.Group && object.userData.isShelfGroup) {
      objectsToRemove.push(object)
    }
  })
  objectsToRemove.forEach((obj) => {
    if (obj instanceof THREE.Sprite) {
      if (obj.material instanceof THREE.SpriteMaterial && obj.material.map) {
        obj.material.map.dispose()
      }
      obj.material.dispose()
    }
    scene.remove(obj)
  })
}

// 缓存的材质（性能优化：复用材质）
const cachedMaterials = {
  pillar: null as THREE.MeshLambertMaterial | null,
  beam: null as THREE.MeshLambertMaterial | null,
  board: null as THREE.MeshLambertMaterial | null,
  cargo: new Map<string, THREE.MeshLambertMaterial>()
}

// 获取或创建材质（复用）
const getMaterial = (type: 'pillar' | 'beam' | 'board', color?: number): THREE.MeshLambertMaterial => {
  if (type === 'pillar' && !cachedMaterials.pillar) {
    cachedMaterials.pillar = new THREE.MeshLambertMaterial({ color: 0x2563eb })
  }
  if (type === 'beam' && !cachedMaterials.beam) {
    cachedMaterials.beam = new THREE.MeshLambertMaterial({ color: 0xf97316 })
  }
  if (type === 'board' && !cachedMaterials.board) {
    cachedMaterials.board = new THREE.MeshLambertMaterial({ color: 0x8b7355 })
  }
  return cachedMaterials[type]!
}

// 获取货物材质（根据热度缓存）
const getCargoMaterial = (heatValue: number): THREE.MeshLambertMaterial => {
  const key = Math.floor(heatValue / 10).toString() // 按10为单位缓存
  if (!cachedMaterials.cargo.has(key)) {
    const baseColor = new THREE.Color(0xd4a76a)
    const hotColor = new THREE.Color(0x8b4513)
    // 使用固定阈值 HEAT_COLOR_CAP 计算颜色比例
    const ratio = Math.min(heatValue / store.HEAT_COLOR_CAP, 1)
    const finalColor = baseColor.clone().lerp(hotColor, ratio * 0.5)
    cachedMaterials.cargo.set(key, new THREE.MeshLambertMaterial({ color: finalColor }))
  }
  return cachedMaterials.cargo.get(key)!
}

// 缓存的几何体（性能优化：复用几何体）
const cachedGeometries = {
  pillar: null as THREE.BoxGeometry | null,
  beam: null as THREE.BoxGeometry | null,
  sideBeam: null as THREE.BoxGeometry | null,
  board: null as THREE.BoxGeometry | null,
  cargo: null as THREE.BoxGeometry | null
}

// 创建简化货架结构（性能优化版）
const createSimpleShelf = (
  shelfWidth: number,
  shelfDepth: number,
  layers: number,
  layerHeight: number
): THREE.Group => {
  const shelfGroup = new THREE.Group()
  shelfGroup.userData.isShelfGroup = true
  
  const totalHeight = layers * layerHeight
  const pillarWidth = 0.1
  
  // 复用几何体
  if (!cachedGeometries.pillar) {
    cachedGeometries.pillar = new THREE.BoxGeometry(pillarWidth, 1, pillarWidth)
  }
  if (!cachedGeometries.beam) {
    cachedGeometries.beam = new THREE.BoxGeometry(1, 0.06, 0.04)
  }
  if (!cachedGeometries.sideBeam) {
    cachedGeometries.sideBeam = new THREE.BoxGeometry(0.04, 0.06, 1)
  }
  if (!cachedGeometries.board) {
    cachedGeometries.board = new THREE.BoxGeometry(1, 0.03, 1)
  }
  
  const pillarMat = getMaterial('pillar')
  const beamMat = getMaterial('beam')
  const boardMat = getMaterial('board')
  
  // 四根立柱
  const pillarPositions = [
    [-shelfWidth/2 + pillarWidth/2, -shelfDepth/2 + pillarWidth/2],
    [shelfWidth/2 - pillarWidth/2, -shelfDepth/2 + pillarWidth/2],
    [-shelfWidth/2 + pillarWidth/2, shelfDepth/2 - pillarWidth/2],
    [shelfWidth/2 - pillarWidth/2, shelfDepth/2 - pillarWidth/2]
  ]
  
  pillarPositions.forEach(([px, pz]) => {
    const pillar = new THREE.Mesh(cachedGeometries.pillar, pillarMat)
    pillar.scale.y = totalHeight + 0.2
    pillar.position.set(px, (totalHeight + 0.2) / 2, pz)
    shelfGroup.add(pillar)
  })
  
  // 每层的横梁和货架板
  for (let layer = 0; layer <= layers; layer++) {
    const layerY = layer * layerHeight
    
    // 前后横梁
    const frontBeam = new THREE.Mesh(cachedGeometries.beam, beamMat)
    frontBeam.scale.x = shelfWidth - pillarWidth * 2
    frontBeam.position.set(0, layerY + 0.03, -shelfDepth/2 + pillarWidth/2)
    shelfGroup.add(frontBeam)
    
    const backBeam = new THREE.Mesh(cachedGeometries.beam, beamMat)
    backBeam.scale.x = shelfWidth - pillarWidth * 2
    backBeam.position.set(0, layerY + 0.03, shelfDepth/2 - pillarWidth/2)
    shelfGroup.add(backBeam)
    
    // 货架板（除了最顶层）
    if (layer < layers) {
      const board = new THREE.Mesh(cachedGeometries.board, boardMat)
      board.scale.set(shelfWidth - pillarWidth * 2 - 0.05, 1, shelfDepth - pillarWidth * 2 - 0.05)
      board.position.set(0, layerY + 0.08, 0)
      shelfGroup.add(board)
    }
  }
  
  return shelfGroup
}

// 创建简化货物（性能优化版：每层只放一个合并的货物块）
const createSimpleCargo = (
  shelfWidth: number,
  shelfDepth: number,
  layer: number,
  layerHeight: number,
  heatValue: number,
  fillRatio: number
): THREE.Mesh | null => {
  if (fillRatio < 0.1) return null
  
  const pillarWidth = 0.1
  const baseY = layer * layerHeight + 0.1
  
  // 可用空间
  const availableWidth = shelfWidth - pillarWidth * 2 - 0.15
  const availableDepth = shelfDepth - pillarWidth * 2 - 0.15
  const cargoHeight = Math.min((layerHeight - 0.15) * fillRatio, layerHeight - 0.2)
  
  // 复用几何体
  if (!cachedGeometries.cargo) {
    cachedGeometries.cargo = new THREE.BoxGeometry(1, 1, 1)
  }
  
  const cargoMat = getCargoMaterial(heatValue)
  const cargo = new THREE.Mesh(cachedGeometries.cargo, cargoMat)
  cargo.scale.set(availableWidth * 0.9, cargoHeight, availableDepth * 0.9)
  cargo.position.set(0, baseY + cargoHeight / 2, 0)
  
  return cargo
}

// 更新场景（渲染货架）- 性能优化版
const updateScene = () => {
  if (!scene || !heatmapData.value) return

  // 清除现有货架（不销毁缓存的几何体和材质）
  shelfMeshes.forEach(({ mesh }) => {
    scene.remove(mesh)
  })
  shelfMeshes.clear()
  
  // 清除标签和货架组
  clearLabels()
  
  // 清除旧地板和网格
  const objectsToRemove: THREE.Object3D[] = []
  scene.traverse((obj) => {
    if (obj.userData.isFloor || obj.userData.isGrid) {
      objectsToRemove.push(obj)
    }
  })
  objectsToRemove.forEach((obj) => scene.remove(obj))

  // 计算布局边界（包含最小值）
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
  
  // 处理空数据情况
  if (minX === Infinity) minX = 0
  if (maxX === -Infinity) maxX = 0
  if (minY === Infinity) minY = 0
  if (maxY === -Infinity) maxY = 0

  const cellSize = 4 // 货架宽度
  const cellDepth = 2.5 // 货架深度
  const gap = 1.2 // 货架间隙（通道）
  const layerHeight = 2 // 每层高度
  
  // 计算实际布局宽度和深度
  const layoutWidth = (maxX - minX + 1) * (cellSize + gap) + cellSize
  const layoutDepth = (maxY - minY + 1) * (cellDepth + gap) + cellDepth
  
  // 存储布局大小供视角切换使用
  currentLayoutSize = { width: layoutWidth, depth: layoutDepth }
  
  // 地板尺寸要比布局大一些（留边距）
  const floorSize = Math.max(layoutWidth, layoutDepth) + 30
  
  // 动态创建网格
  const gridHelper = new THREE.GridHelper(floorSize, Math.floor(floorSize / 5), 0xcccccc, 0xe0e0e0)
  gridHelper.userData.isGrid = true
  scene.add(gridHelper)
  
  // 动态创建地板
  const floorGeometry = new THREE.PlaneGeometry(floorSize, floorSize)
  const floorMaterial = new THREE.MeshLambertMaterial({ color: 0xeeeeee })
  const floor = new THREE.Mesh(floorGeometry, floorMaterial)
  floor.rotation.x = -Math.PI / 2
  floor.position.y = -0.01
  floor.userData.isFloor = true
  scene.add(floor)
  
  // 计算偏移量，使布局居中
  const offsetX = ((minX + maxX) / 2) * (cellSize + gap)
  const offsetZ = ((minY + maxY) / 2) * (cellDepth + gap)

  // 渲染货架
  heatmapData.value.aisles.forEach((aisle: any) => {
    aisle.shelves.forEach((shelf: any) => {
      const maxHeat = getShelfMaxHeat(shelf.locations)
      const avgHeat = getShelfAvgHeat(shelf.locations)
      const totalInventory = getTotalInventory(shelf.locations)
      const layers = shelf.layers || 1

      const posX = shelf.x_coordinate * (cellSize + gap) - offsetX
      const posZ = aisle.y_coordinate * (cellDepth + gap) - offsetZ

      // 创建简化货架结构
      const shelfGroup = createSimpleShelf(cellSize, cellDepth, layers, layerHeight)
      shelfGroup.position.set(posX, 0, posZ)
      scene.add(shelfGroup)

      // 为每层添加简化货物
      const fillRatio = Math.max(0.3, Math.min(1, (maxHeat / store.HEAT_COLOR_CAP) + 0.3))
      
      for (let layer = 0; layer < layers; layer++) {
        const cargo = createSimpleCargo(
          cellSize,
          cellDepth,
          layer,
          layerHeight,
          maxHeat,
          fillRatio
        )
        if (cargo) {
          cargo.position.x += posX
          cargo.position.z += posZ
          scene.add(cargo)
        }
      }

      // 创建不可见的点击区域（用于交互）
      const totalHeight = layers * layerHeight
      const hitboxGeometry = new THREE.BoxGeometry(cellSize, totalHeight, cellDepth)
      const hitboxMaterial = new THREE.MeshBasicMaterial({
        transparent: true,
        opacity: 0,
        depthWrite: false
      })
      const hitbox = new THREE.Mesh(hitboxGeometry, hitboxMaterial)
      hitbox.position.set(posX, totalHeight / 2, posZ)
      scene.add(hitbox)

      // 存储数据关联
      const shelfData = {
        ...shelf,
        aisle_code: aisle.aisle_code,
        maxHeat,
        avgHeat,
        totalInventory,
        layers
      }
      shelfMeshes.set(hitbox.uuid, { mesh: hitbox, data: shelfData })

      // 添加标签
      addLabel(hitbox, shelf.shelf_name || `${aisle.aisle_code}-${shelf.shelf_code}`, totalHeight, layers)
    })
  })

  // 根据布局大小调整相机位置
  const viewDistance = Math.max(layoutWidth, layoutDepth) * 0.8
  camera.position.set(viewDistance * 0.7, viewDistance * 0.5, viewDistance * 0.9)
  controls.target.set(0, 0, 0)
  controls.update()
}

// 添加标签
const addLabel = (mesh: THREE.Mesh, text: string, height: number, layers: number = 1) => {
  // 使用 CSS2D 或 sprite 来显示标签（这里用简单的 sprite）
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')!
  canvas.width = 160
  canvas.height = 48
  
  // 清除背景
  context.clearRect(0, 0, canvas.width, canvas.height)
  
  // 绘制名称
  context.fillStyle = '#333333'
  context.font = 'bold 18px Arial'
  context.textAlign = 'center'
  context.textBaseline = 'middle'
  context.fillText(text.slice(0, 12), 80, 16)
  
  // 如果有多层，显示层数
  if (layers > 1) {
    context.fillStyle = '#666666'
    context.font = '14px Arial'
    context.fillText(`${layers} 层`, 80, 36)
  }

  const texture = new THREE.CanvasTexture(canvas)
  const spriteMaterial = new THREE.SpriteMaterial({ map: texture })
  const sprite = new THREE.Sprite(spriteMaterial)
  sprite.scale.set(5, 1.5, 1)
  sprite.position.set(mesh.position.x, height + 1.5, mesh.position.z)
  scene.add(sprite)
}

// 动画循环
const animate = () => {
  animationId = requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

// 鼠标移动
const onMouseMove = (event: MouseEvent) => {
  if (!sceneRef.value) return

  const rect = sceneRef.value.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const meshArray = Array.from(shelfMeshes.values()).map(item => item.mesh)
  const intersects = raycaster.intersectObjects(meshArray)

  if (intersects.length > 0) {
    const intersected = intersects[0].object as THREE.Mesh
    const shelfInfo = shelfMeshes.get(intersected.uuid)
    if (shelfInfo) {
      hoverShelf.value = shelfInfo.data
      tooltipX.value = event.clientX + 15
      tooltipY.value = event.clientY + 15
      tooltipVisible.value = true
      document.body.style.cursor = 'pointer'
    }
  } else {
    tooltipVisible.value = false
    hoverShelf.value = null
    document.body.style.cursor = 'default'
  }
}

// 鼠标点击
const onMouseClick = (event: MouseEvent) => {
  if (!sceneRef.value) return

  const rect = sceneRef.value.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const meshArray = Array.from(shelfMeshes.values()).map(item => item.mesh)
  const intersects = raycaster.intersectObjects(meshArray)

  if (intersects.length > 0) {
    const intersected = intersects[0].object as THREE.Mesh
    const shelfInfo = shelfMeshes.get(intersected.uuid)
    if (shelfInfo) {
      selectedShelf.value = shelfInfo.data
      detailDialogVisible.value = true
    }
  }
}

// 窗口大小变化
const onWindowResize = () => {
  if (!sceneRef.value || !camera || !renderer) return

  const width = sceneRef.value.clientWidth
  const height = sceneRef.value.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// 设置视角
const setView = (view: string) => {
  activeView.value = view
  
  // 根据布局大小计算合适的视距
  const viewDistance = Math.max(currentLayoutSize.width, currentLayoutSize.depth) * 0.8
  
  switch (view) {
    case 'top':
      camera.position.set(0, viewDistance * 1.2, 0.1)
      break
    case 'front':
      camera.position.set(0, viewDistance * 0.3, viewDistance)
      break
    case 'side':
      camera.position.set(viewDistance, viewDistance * 0.3, 0)
      break
    case 'perspective':
      camera.position.set(viewDistance * 0.7, viewDistance * 0.5, viewDistance * 0.9)
      break
  }
  
  controls.target.set(0, 0, 0)
  controls.update()
}

// 重置相机
const resetCamera = () => {
  setView('perspective')
}

// 查询
const handleSearch = () => {
  store.loadHeatmapData()
}

// 仓库变更
const handleWarehouseChange = async (warehouseId: number) => {
  await store.loadZones(warehouseId)
  if (store.zones.length > 0) {
    selectedZone.value = store.zones[0].id
    await store.loadHeatmapData()
  } else {
    selectedZone.value = null
  }
}

// 监听库区变化
watch(selectedZone, (newVal) => {
  if (newVal !== null) {
    store.setZone(newVal)
  }
})

// 监听数据变化，更新场景
watch(heatmapData, () => {
  nextTick(() => {
    updateScene()
  })
})

// 清理资源
const cleanup = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  
  if (sceneRef.value) {
    sceneRef.value.removeEventListener('mousemove', onMouseMove)
    sceneRef.value.removeEventListener('click', onMouseClick)
  }
  window.removeEventListener('resize', onWindowResize)
  
  shelfMeshes.forEach(({ mesh }) => {
    mesh.geometry.dispose()
    if (mesh.material instanceof THREE.Material) {
      mesh.material.dispose()
    }
  })
  shelfMeshes.clear()
  
  if (renderer) {
    renderer.dispose()
  }
}

// 生命周期
onMounted(async () => {
  // 加载仓库列表
  try {
    warehouses.value = await warehouseApi.getWarehouses()
    if (warehouses.value.length > 0) {
      selectedWarehouse.value = warehouses.value[0].id
      await store.loadZones(warehouses.value[0].id)
      if (store.zones.length > 0) {
        selectedZone.value = 0
        store.setZone(0)
      }
    }
  } catch (error) {
    console.error('初始化失败:', error)
  }

  // 初始化 Three.js 场景
  await nextTick()
  initScene()
})

onUnmounted(() => {
  cleanup()
})
</script>

<style lang="scss" scoped>
.heatmap-3d-page {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.page-tabs {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-section {
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

  .legend-tip {
    font-size: 12px;
    color: #999;
  }
}

.scene-container {
  position: relative;
  height: calc(100vh - 220px);
  min-height: 400px;
  overflow: hidden;

  .three-scene {
    width: 100%;
    height: 100%;
  }

  .view-controls {
    position: absolute;
    top: 15px;
    right: 15px;
    z-index: 10;
  }

  .controls-hint {
    position: absolute;
    bottom: 15px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 10;
  }
}

.hover-tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  z-index: 9999;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

  div {
    line-height: 1.8;
  }
}

.shelf-detail {
  .detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    h3 {
      margin: 0;
      font-size: 18px;
    }
  }

  .detail-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;

    .stat-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 15px;
      background: #f5f7fa;
      border-radius: 8px;

      .stat-label {
        font-size: 12px;
        color: #909399;
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #303133;
        
        &.highlight {
          color: #409eff;
        }
      }
    }
  }

  .locations-grid {
    .grid-title {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 12px;
      color: #606266;
    }

    .location-items {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;

      .location-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 8px 12px;
        border-radius: 4px;
        min-width: 60px;

        .loc-code {
          font-size: 12px;
          font-weight: 500;
          color: #333;
        }

        .loc-heat {
          font-size: 10px;
          color: #666;
        }
      }
    }
  }
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}
</style>
