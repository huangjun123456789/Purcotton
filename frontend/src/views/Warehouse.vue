<template>
  <div class="warehouse-page page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>仓库管理</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建仓库
          </el-button>
        </div>
      </template>

      <el-table :data="warehouses" v-loading="loading" style="width: 100%">
        <el-table-column prop="code" label="仓库编码" width="150" />
        <el-table-column prop="name" label="仓库名称" width="200" />
        <el-table-column prop="address" label="地址" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button type="primary" link @click="editWarehouse(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-dropdown @command="(cmd: string) => handleLayoutCommand(cmd, row)">
              <el-button type="primary" link>
                <el-icon><Grid /></el-icon>
                布局
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="canvas">
                    <el-icon><EditPen /></el-icon>
                    画布模式
                  </el-dropdown-item>
                  <el-dropdown-item command="quick">
                    <el-icon><MagicStick /></el-icon>
                    快速生成
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑仓库' : '新建仓库'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="仓库编码" prop="code">
          <el-input v-model="formData.code" :disabled="isEdit" placeholder="请输入仓库编码" />
        </el-form-item>
        <el-form-item label="仓库名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入仓库名称" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="formData.address" placeholder="请输入仓库地址" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 仓库详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="仓库详情"
      width="800px"
    >
      <el-descriptions :column="2" border v-if="currentWarehouse">
        <el-descriptions-item label="仓库编码">{{ currentWarehouse.code }}</el-descriptions-item>
        <el-descriptions-item label="仓库名称">{{ currentWarehouse.name }}</el-descriptions-item>
        <el-descriptions-item label="地址" :span="2">{{ currentWarehouse.address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentWarehouse.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentWarehouse.is_active ? 'success' : 'info'">
            {{ currentWarehouse.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(currentWarehouse.created_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">库区列表</el-divider>
      
      <el-table :data="currentZones" style="width: 100%">
        <el-table-column prop="code" label="库区编码" width="120" />
        <el-table-column prop="name" label="库区名称" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 布局设置弹窗 -->
    <el-dialog
      v-model="layoutDialogVisible"
      title="仓库布局设置"
      width="900px"
    >
      <el-alert
        title="快速设置仓库布局"
        description="您可以在此快速创建库区、巷道和货架。系统会自动生成对应的库位。"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-form :model="layoutForm" label-width="100px">
        <el-form-item label="库区数量">
          <el-input-number v-model="layoutForm.zoneCount" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="每区巷道数">
          <el-input-number v-model="layoutForm.aisleCount" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="每巷货架数">
          <el-input-number v-model="layoutForm.shelfCount" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="货架行数">
          <el-input-number v-model="layoutForm.shelfRows" :min="1" :max="26" />
        </el-form-item>
        <el-form-item label="货架列数">
          <el-input-number v-model="layoutForm.shelfColumns" :min="1" :max="20" />
        </el-form-item>
      </el-form>

      <el-divider />

      <div class="layout-preview">
        <h4>预览：将生成 {{ totalLocations }} 个库位</h4>
        <p>
          {{ layoutForm.zoneCount }} 个库区 × 
          {{ layoutForm.aisleCount }} 个巷道 × 
          {{ layoutForm.shelfCount }} 个货架 × 
          {{ layoutForm.shelfRows }} 行 × 
          {{ layoutForm.shelfColumns }} 列
        </p>
      </div>

      <template #footer>
        <el-button @click="layoutDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleLayoutSubmit" :loading="layoutSubmitting">
          生成布局
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { warehouseApi } from '@/api'
import type { Warehouse, Zone } from '@/types'
import dayjs from 'dayjs'

const router = useRouter()

// 状态
const loading = ref(false)
const submitting = ref(false)
const layoutSubmitting = ref(false)
const warehouses = ref<Warehouse[]>([])
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const layoutDialogVisible = ref(false)
const isEdit = ref(false)
const currentWarehouse = ref<Warehouse | null>(null)
const currentZones = ref<Zone[]>([])

const formRef = ref<FormInstance>()
const formData = reactive({
  id: 0,
  code: '',
  name: '',
  address: '',
  description: ''
})

const formRules: FormRules = {
  code: [{ required: true, message: '请输入仓库编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入仓库名称', trigger: 'blur' }]
}

// 从 localStorage 读取上次的布局配置
const getStoredLayoutConfig = () => {
  try {
    const stored = localStorage.getItem('warehouseLayoutConfig')
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error('读取布局配置失败:', e)
  }
  return {
    zoneCount: 1,
    aisleCount: 2,
    shelfCount: 4,
    shelfRows: 4,
    shelfColumns: 5
  }
}

const layoutForm = reactive(getStoredLayoutConfig())

// 保存布局配置到 localStorage
const saveLayoutConfig = () => {
  try {
    localStorage.setItem('warehouseLayoutConfig', JSON.stringify({
      zoneCount: layoutForm.zoneCount,
      aisleCount: layoutForm.aisleCount,
      shelfCount: layoutForm.shelfCount,
      shelfRows: layoutForm.shelfRows,
      shelfColumns: layoutForm.shelfColumns
    }))
  } catch (e) {
    console.error('保存布局配置失败:', e)
  }
}

// 监听布局配置变化，自动保存
watch(layoutForm, () => {
  saveLayoutConfig()
}, { deep: true })

const totalLocations = computed(() => {
  return layoutForm.zoneCount * layoutForm.aisleCount * layoutForm.shelfCount * 
         layoutForm.shelfRows * layoutForm.shelfColumns
})

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 加载仓库列表
const loadWarehouses = async () => {
  loading.value = true
  try {
    warehouses.value = await warehouseApi.getWarehouses()
  } catch (error) {
    ElMessage.error('加载仓库列表失败')
  } finally {
    loading.value = false
  }
}

// 显示创建弹窗
const showCreateDialog = () => {
  isEdit.value = false
  formData.id = 0
  formData.code = ''
  formData.name = ''
  formData.address = ''
  formData.description = ''
  dialogVisible.value = true
}

// 编辑仓库
const editWarehouse = (row: Warehouse) => {
  isEdit.value = true
  formData.id = row.id
  formData.code = row.code
  formData.name = row.name
  formData.address = row.address || ''
  formData.description = row.description || ''
  dialogVisible.value = true
}

// 查看详情
const viewDetail = async (row: Warehouse) => {
  currentWarehouse.value = row
  try {
    currentZones.value = await warehouseApi.getZones(row.id)
  } catch (error) {
    currentZones.value = []
  }
  detailDialogVisible.value = true
}

// 处理布局命令
const handleLayoutCommand = (command: string, row: Warehouse) => {
  if (command === 'canvas') {
    // 画布模式
    router.push(`/warehouse/${row.id}/canvas`)
  } else if (command === 'quick') {
    // 快速生成模式
    currentWarehouse.value = row
    layoutDialogVisible.value = true
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          await warehouseApi.updateWarehouse(formData.id, {
            name: formData.name,
            address: formData.address,
            description: formData.description
          })
          ElMessage.success('更新成功')
        } else {
          await warehouseApi.createWarehouse({
            code: formData.code,
            name: formData.name,
            address: formData.address,
            description: formData.description
          })
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadWarehouses()
      } catch (error) {
        ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 提交布局
const handleLayoutSubmit = async () => {
  if (!currentWarehouse.value) return

  await ElMessageBox.confirm(
    `确定要为仓库 "${currentWarehouse.value.name}" 生成 ${totalLocations.value} 个库位吗？`,
    '确认生成',
    { type: 'warning' }
  )

  layoutSubmitting.value = true
  try {
    // 构建配置
    const zonesConfig = []
    for (let z = 0; z < layoutForm.zoneCount; z++) {
      const zoneCode = String.fromCharCode(65 + z) // A, B, C...
      const aisles = []
      
      for (let a = 0; a < layoutForm.aisleCount; a++) {
        const aisleCode = `${String(a + 1).padStart(2, '0')}巷`
        const shelves = []
        
        for (let s = 0; s < layoutForm.shelfCount; s++) {
          shelves.push({
            code: `货架${String(s + 1).padStart(2, '0')}`,
            name: `货架${String(s + 1).padStart(2, '0')}`,
            shelf_type: 'normal',
            rows: layoutForm.shelfRows,
            columns: layoutForm.shelfColumns,
            x_coordinate: s
          })
        }
        
        aisles.push({
          code: aisleCode,
          name: aisleCode,
          y_coordinate: a,
          shelves
        })
      }
      
      zonesConfig.push({
        code: zoneCode,
        name: `${zoneCode}库区`,
        aisles
      })
    }

    await warehouseApi.setupWarehouseLayout(
      currentWarehouse.value.code,
      currentWarehouse.value.name,
      zonesConfig
    )
    
    ElMessage.success('布局生成成功')
    layoutDialogVisible.value = false
    loadWarehouses()
  } catch (error: any) {
    console.error('布局生成失败:', error)
    const errorMsg = error?.response?.data?.detail || error?.message || '布局生成失败'
    ElMessage.error(errorMsg)
  } finally {
    layoutSubmitting.value = false
  }
}

onMounted(() => {
  loadWarehouses()
})
</script>

<style lang="scss" scoped>
.warehouse-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .layout-preview {
    text-align: center;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 4px;
    
    h4 {
      margin: 0 0 10px 0;
      color: #409eff;
    }
    
    p {
      margin: 0;
      color: #666;
    }
  }
}
</style>
