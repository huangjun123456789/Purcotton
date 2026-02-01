<template>
  <el-container class="layout-container">
    <!-- 顶部导航 -->
    <el-header class="header">
      <div class="header-left">
        <div class="logo">
          <el-icon :size="24"><DataBoard /></el-icon>
          <span class="logo-text">WMS 仓库热力图系统</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          router
          class="nav-menu"
          :ellipsis="false"
        >
          <el-sub-menu index="/heatmap-group">
            <template #title>
              <el-icon><PictureFilled /></el-icon>
              <span>库位分布</span>
            </template>
            <el-menu-item index="/heatmap">
              <el-icon><Grid /></el-icon>
              <span>2D 视图</span>
            </el-menu-item>
            <el-menu-item index="/heatmap3d">
              <el-icon><Box /></el-icon>
              <span>3D 视图</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-if="isAdmin" index="/warehouse">
            <el-icon><OfficeBuilding /></el-icon>
            <span>仓库管理</span>
          </el-menu-item>
          <el-menu-item v-if="isAdmin" index="/import">
            <el-icon><Upload /></el-icon>
            <span>数据导入</span>
          </el-menu-item>
          <el-menu-item v-if="isAdmin" index="/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
        </el-menu>
      </div>
      <div class="header-right">
        <el-button type="primary" link>
          <el-icon><Refresh /></el-icon>
          订单同步
        </el-button>
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32" icon="UserFilled" />
            <span class="username">{{ displayName }}</span>
            <el-tag size="small" :type="isAdmin ? 'danger' : 'info'" class="role-tag">
              {{ isAdmin ? '管理员' : '用户' }}
            </el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="settings">
                <el-icon><Setting /></el-icon>
                个人设置
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <!-- 主内容区 -->
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { User, Setting, SwitchButton, Grid, Box } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const isAdmin = computed(() => userStore.isAdmin)
const displayName = computed(() => userStore.displayName)

const handleCommand = async (command: string) => {
  switch (command) {
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await userStore.logout()
        ElMessage.success('已退出登录')
        router.push('/login')
      } catch (error) {
        // 用户取消
      }
      break
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100vh;
  background-color: #f5f7fa;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
  height: 60px !important;

  .header-left {
    display: flex;
    align-items: center;
    gap: 30px;

    .logo {
      display: flex;
      align-items: center;
      gap: 10px;
      color: #409eff;

      .logo-text {
        font-size: 18px;
        font-weight: bold;
        color: #303133;
      }
    }

    .nav-menu {
      border-bottom: none;

      :deep(.el-menu-item) {
        height: 60px;
        line-height: 60px;
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;

      .username {
        font-size: 14px;
        color: #606266;
      }
      
      .role-tag {
        margin-left: 4px;
      }
    }
  }
}

.main-content {
  padding: 0;
  overflow: hidden;
}
</style>
