import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { HeatmapData, HeatmapFilterParams, Zone, TimeRange, ShelfType } from '@/types'
import { heatmapApi, warehouseApi } from '@/api'

export const useHeatmapStore = defineStore('heatmap', () => {
  // 状态
  const loading = ref(false)
  const heatmapData = ref<HeatmapData | null>(null)
  const zones = ref<Zone[]>([])
  const selectedZoneId = ref<number | null>(null)
  const filterParams = ref<HeatmapFilterParams>({
    time_range: 'all',
    shelf_type: undefined,
    start_date: undefined,
    end_date: undefined
  })

  // 计算属性
  const maxHeatValue = computed(() => heatmapData.value?.max_heat || 0)
  const minHeatValue = computed(() => heatmapData.value?.min_heat || 0)
  
  // 热力值颜色映射上限阈值（超过此值都显示为最高频颜色）
  const HEAT_COLOR_CAP = 1000

  // 获取颜色
  const getHeatColor = (value: number): string => {
    if (value === 0) return '#ffffcc'
    
    // 使用固定上限阈值计算颜色比例，超过阈值的都显示最高频颜色
    const ratio = Math.min(value / HEAT_COLOR_CAP, 1)
    
    // 热力图颜色梯度: 浅黄 -> 橙色 -> 红色 -> 深红
    const colors = [
      { pos: 0, r: 255, g: 255, b: 204 },     // #ffffcc
      { pos: 0.25, r: 254, g: 217, b: 118 },  // #fed976
      { pos: 0.5, r: 253, g: 141, b: 60 },    // #fd8d3c
      { pos: 0.75, r: 227, g: 26, b: 28 },    // #e31a1c
      { pos: 1, r: 128, g: 0, b: 38 }         // #800026
    ]
    
    // 找到对应的颜色区间
    let startColor = colors[0]
    let endColor = colors[colors.length - 1]
    
    for (let i = 0; i < colors.length - 1; i++) {
      if (ratio >= colors[i].pos && ratio <= colors[i + 1].pos) {
        startColor = colors[i]
        endColor = colors[i + 1]
        break
      }
    }
    
    // 插值计算
    const rangeRatio = (ratio - startColor.pos) / (endColor.pos - startColor.pos)
    const r = Math.round(startColor.r + (endColor.r - startColor.r) * rangeRatio)
    const g = Math.round(startColor.g + (endColor.g - startColor.g) * rangeRatio)
    const b = Math.round(startColor.b + (endColor.b - startColor.b) * rangeRatio)
    
    return `rgb(${r}, ${g}, ${b})`
  }

  // 加载库区列表
  const loadZones = async (warehouseId: number) => {
    try {
      zones.value = await warehouseApi.getZones(warehouseId)
      if (zones.value.length > 0 && !selectedZoneId.value) {
        selectedZoneId.value = zones.value[0].id
      }
    } catch (error) {
      console.error('加载库区失败:', error)
    }
  }

  // 加载热力图数据
  const loadHeatmapData = async () => {
    if (selectedZoneId.value === null) return
    
    loading.value = true
    try {
      if (selectedZoneId.value === 0) {
        // 加载全部库区数据
        const allAisles: any[] = []
        let maxHeat = 0
        let minHeat = Infinity
        let lastTimeRange = filterParams.value.time_range || 'today'
        let lastStartDate = ''
        let lastEndDate = ''
        
        for (const zone of zones.value) {
          const zoneData = await heatmapApi.getHeatmapData(zone.id, filterParams.value)
          if (zoneData && zoneData.aisles) {
            // 保持原始坐标位置，只添加库区标识
            zoneData.aisles.forEach((aisle: any) => {
              aisle.zone_name = zone.name
              allAisles.push(aisle)
            })
            if (zoneData.max_heat > maxHeat) maxHeat = zoneData.max_heat
            if (zoneData.min_heat < minHeat) minHeat = zoneData.min_heat
            lastTimeRange = zoneData.time_range
            lastStartDate = zoneData.start_date
            lastEndDate = zoneData.end_date
          }
        }
        
        heatmapData.value = {
          zone_id: 0,
          zone_code: 'ALL',
          zone_name: '全部库区',
          aisles: allAisles,
          max_heat: maxHeat,
          min_heat: minHeat === Infinity ? 0 : minHeat,
          time_range: lastTimeRange,
          start_date: lastStartDate,
          end_date: lastEndDate
        } as HeatmapData
      } else {
        // 加载单个库区数据
        heatmapData.value = await heatmapApi.getHeatmapData(
          selectedZoneId.value,
          filterParams.value
        )
      }
    } catch (error) {
      console.error('加载热力图数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 更新筛选参数
  const updateFilter = (params: Partial<HeatmapFilterParams>) => {
    filterParams.value = { ...filterParams.value, ...params }
    loadHeatmapData()
  }

  // 设置时间范围
  const setTimeRange = (range: TimeRange) => {
    updateFilter({ time_range: range })
  }

  // 设置货架类型
  const setShelfType = (type: ShelfType | undefined) => {
    updateFilter({ shelf_type: type })
  }

  // 设置库区 (0 = 全部库区)
  const setZone = (zoneId: number) => {
    selectedZoneId.value = zoneId
    loadHeatmapData()
  }

  return {
    // 状态
    loading,
    heatmapData,
    zones,
    selectedZoneId,
    filterParams,
    // 计算属性
    maxHeatValue,
    minHeatValue,
    // 常量
    HEAT_COLOR_CAP,
    // 方法
    getHeatColor,
    loadZones,
    loadHeatmapData,
    updateFilter,
    setTimeRange,
    setShelfType,
    setZone
  }
})
