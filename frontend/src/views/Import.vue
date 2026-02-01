<template>
  <div class="import-page page-container">
    <el-row :gutter="20">
      <!-- 上传区域 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>数据导入</span>
          </template>

          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            accept=".xlsx,.xls,.csv"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xlsx, .xls, .csv 格式文件
              </div>
            </template>
          </el-upload>

          <div class="upload-actions" v-if="selectedFile">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="文件名">{{ selectedFile.name }}</el-descriptions-item>
              <el-descriptions-item label="文件大小">{{ formatFileSize(selectedFile.size) }}</el-descriptions-item>
              <el-descriptions-item label="文件类型">{{ getFileType(selectedFile.name) }}</el-descriptions-item>
            </el-descriptions>
            
            <div class="action-buttons">
              <el-button @click="clearFile">清除</el-button>
              <el-button type="primary" @click="handleUpload" :loading="uploading">
                <el-icon><Upload /></el-icon>
                开始导入
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 模板下载和说明 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>模板下载</span>
          </template>

          <div class="template-section">
            <p>请先下载导入模板，按照模板格式填写数据后上传。</p>
            
            <div class="template-buttons">
              <el-button type="primary" @click="downloadTemplate('excel')">
                <el-icon><Download /></el-icon>
                下载 Excel 模板
              </el-button>
              <el-button @click="downloadTemplate('csv')">
                <el-icon><Download /></el-icon>
                下载 CSV 模板
              </el-button>
            </div>
          </div>

          <el-divider />

          <div class="field-description">
            <h4>字段说明</h4>
            <el-table :data="fieldDescriptions" style="width: 100%" size="small">
              <el-table-column prop="field" label="字段名" width="120" />
              <el-table-column prop="required" label="必填" width="60">
                <template #default="{ row }">
                  <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                    {{ row.required ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="说明" />
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 导入结果 -->
    <el-card v-if="importResult" class="result-card">
      <template #header>
        <span>导入结果</span>
      </template>

      <el-result
        :icon="importResult.success ? 'success' : 'warning'"
        :title="importResult.success ? '导入完成' : '导入部分完成'"
      >
        <template #sub-title>
          <div class="result-stats">
            <el-statistic title="总行数" :value="importResult.total_rows" />
            <el-statistic title="成功导入" :value="importResult.imported_rows" class="success" />
            <el-statistic v-if="importResult.skipped_rows" title="跳过行数" :value="importResult.skipped_rows" class="warning" />
            <el-statistic title="失败行数" :value="importResult.failed_rows" class="danger" />
          </div>
        </template>
        
        <template #extra>
          <!-- 日期范围提示 -->
          <div v-if="importResult.date_range" class="date-range-info">
            <el-alert
              type="info"
              :closable="false"
              show-icon
            >
              <template #title>
                <span>导入数据日期范围: {{ importResult.date_range.start_date }} 至 {{ importResult.date_range.end_date }}</span>
              </template>
              <template #default>
                <p style="margin: 5px 0 0 0;">查看热力图时，请确保选择包含此日期范围的筛选条件</p>
                <el-button 
                  type="primary" 
                  size="small" 
                  style="margin-top: 10px;"
                  @click="goToHeatmap"
                >
                  前往库位分布页面查看
                </el-button>
              </template>
            </el-alert>
          </div>
          
          <!-- 错误/提示详情 -->
          <div v-if="importResult.errors && importResult.errors.length > 0" class="error-section">
            <el-button type="warning" @click="showErrorDialog = true">
              <el-icon><Warning /></el-icon>
              查看详情（{{ importResult.errors.length }} 条信息）
            </el-button>
          </div>
        </template>
      </el-result>
    </el-card>

    <!-- 错误详情对话框 -->
    <el-dialog
      v-model="showErrorDialog"
      title="导入详情"
      width="600px"
      :close-on-click-modal="true"
    >
      <div class="error-dialog-content">
        <ul class="error-list">
          <li v-for="(error, index) in importResult?.errors" :key="index">
            {{ error }}
          </li>
        </ul>
      </div>
      <template #footer>
        <el-button type="primary" @click="showErrorDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 导入历史 -->
    <el-card class="history-card" v-loading="historyLoading">
      <template #header>
        <div class="history-header">
          <span>最近导入记录</span>
          <el-button text type="primary" @click="loadImportHistory" :loading="historyLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="importHistory" style="width: 100%">
        <el-table-column prop="filename" label="文件名" min-width="180" />
        <el-table-column prop="import_time" label="导入时间" width="180" />
        <el-table-column prop="total_rows" label="总行数" width="100" />
        <el-table-column prop="success_rows" label="成功数" width="100" />
        <el-table-column prop="failed_rows" label="失败数" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="importHistory.length === 0 && !historyLoading" description="暂无导入记录" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadInstance, UploadRawFile } from 'element-plus'
import { importApi, type ImportHistoryItem } from '@/api'
import type { ImportResult } from '@/types'

const router = useRouter()
const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const importResult = ref<ImportResult | null>(null)
const historyLoading = ref(false)
const showErrorDialog = ref(false)

// 字段说明
const fieldDescriptions = [
  { field: '库位编码', required: true, description: '完整的库位编码（下载模板查看实际格式）' },
  { field: '日期', required: true, description: '统计日期，格式：YYYY-MM-DD' },
  { field: '拣货频率', required: true, description: '该库位的拣货次数' },
  { field: '周转率', required: false, description: '库存周转率（0-1之间的小数）' },
  { field: '库存数量', required: false, description: '当前库存数量' },
  { field: '入库数量', required: false, description: '入库数量' },
  { field: '出库数量', required: false, description: '出库数量' }
]

// 导入历史
const importHistory = ref<ImportHistoryItem[]>([])

// 加载导入历史
const loadImportHistory = async () => {
  historyLoading.value = true
  try {
    importHistory.value = await importApi.getImportHistory(20)
  } catch (error) {
    console.error('加载导入历史失败:', error)
  } finally {
    historyLoading.value = false
  }
}

// 文件变化处理
const handleFileChange = (uploadFile: UploadFile) => {
  selectedFile.value = uploadFile.raw as File
}

// 超出限制处理
const handleExceed = (files: File[]) => {
  uploadRef.value?.clearFiles()
  const file = files[0]
  selectedFile.value = file
}

// 清除文件
const clearFile = () => {
  selectedFile.value = null
  uploadRef.value?.clearFiles()
  importResult.value = null
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 获取文件类型
const getFileType = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'xlsx':
    case 'xls':
      return 'Excel 文件'
    case 'csv':
      return 'CSV 文件'
    default:
      return '未知'
  }
}

// 上传处理
const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  importResult.value = null

  try {
    const ext = selectedFile.value.name.split('.').pop()?.toLowerCase()
    let result: ImportResult

    if (ext === 'csv') {
      result = await importApi.importCsv(selectedFile.value)
    } else {
      result = await importApi.importExcel(selectedFile.value)
    }

    importResult.value = result

    if (result.success) {
      ElMessage.success(`导入成功：${result.imported_rows} 条记录`)
    } else {
      ElMessage.warning('导入完成，但存在部分错误')
    }
    
    // 刷新导入历史
    await loadImportHistory()
  } catch (error) {
    ElMessage.error('导入失败')
  } finally {
    uploading.value = false
  }
}

// 下载模板
const downloadTemplate = async (type: 'excel' | 'csv') => {
  try {
    let blob: Blob
    let filename: string

    if (type === 'excel') {
      blob = await importApi.downloadExcelTemplate()
      filename = 'heat_data_template.xlsx'
    } else {
      blob = await importApi.downloadCsvTemplate()
      filename = 'heat_data_template.csv'
    }

    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('模板下载成功')
  } catch (error) {
    ElMessage.error('模板下载失败')
  }
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'success': return 'success'
    case 'partial': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

// 获取状态显示文字
const getStatusText = (status: string) => {
  switch (status) {
    case 'success': return '成功'
    case 'partial': return '部分成功'
    case 'failed': return '失败'
    default: return '未知'
  }
}

// 前往热力图页面
const goToHeatmap = () => {
  router.push('/heatmap')
}

// 初始化
onMounted(() => {
  loadImportHistory()
})
</script>

<style lang="scss" scoped>
.import-page {
  .upload-area {
    width: 100%;
    
    :deep(.el-upload-dragger) {
      width: 100%;
    }
  }

  .upload-actions {
    margin-top: 20px;
    
    .action-buttons {
      margin-top: 15px;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
  }

  .template-section {
    p {
      color: #666;
      margin-bottom: 15px;
    }

    .template-buttons {
      display: flex;
      gap: 10px;
    }
  }

  .field-description {
    h4 {
      margin: 0 0 15px 0;
      color: #303133;
    }
  }

  .result-card {
    margin-top: 20px;

    .result-stats {
      display: flex;
      gap: 40px;
      justify-content: center;
      
      :deep(.el-statistic) {
        text-align: center;
        
        &.success .el-statistic__number {
          color: #67c23a;
        }
        
        &.warning .el-statistic__number {
          color: #e6a23c;
        }
        
        &.danger .el-statistic__number {
          color: #f56c6c;
        }
      }
    }
    
    .error-section {
      margin-top: 15px;
      text-align: center;
    }

    .error-list {
      list-style: none;
      padding: 0;
      margin: 0;
      max-height: 300px;
      overflow-y: auto;
      
      li {
        padding: 8px 12px;
        margin-bottom: 8px;
        background: #fef0f0;
        border-radius: 4px;
        color: #f56c6c;
        font-size: 14px;
        
        &:first-child {
          background: #fdf6ec;
          color: #e6a23c;
        }
        
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
  
  .error-dialog-content {
    .error-list {
      max-height: 400px;
    }
    
    .date-range-info {
      max-width: 500px;
      margin: 0 auto;
    }
  }

  .history-card {
    margin-top: 20px;
    
    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
}
</style>
