# 仓库库位热力图系统 (Warehouse Location Heatmap)

一个用于可视化仓库库位热度的全栈应用，帮助仓库管理人员快速识别高频使用的库位。

## 技术栈

### 前端
- **框架**: Vue.js 3 + TypeScript
- **可视化**: ECharts 5
- **UI 组件**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite

### 后端
- **框架**: Python FastAPI
- **ORM**: SQLAlchemy
- **数据验证**: Pydantic
- **异步支持**: asyncio + aiofiles

### 数据库
- **数据库**: MySQL 8.0 / PostgreSQL 14+

## 项目结构

```
XM-03-RLT/
├── frontend/                 # Vue.js 前端
│   ├── src/
│   │   ├── components/       # 可复用组件
│   │   ├── views/            # 页面视图
│   │   ├── api/              # API 调用
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── types/            # TypeScript 类型定义
│   │   └── utils/            # 工具函数
│   └── package.json
├── backend/                  # Python 后端
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── models/           # 数据模型
│   │   ├── schemas/          # Pydantic 模式
│   │   ├── services/         # 业务逻辑
│   │   └── utils/            # 工具函数
│   ├── requirements.txt
│   └── main.py
├── database/                 # 数据库脚本
│   └── init.sql
└── README.md
```

## 功能特性

### 1. 库位建模器
- 支持自定义仓库布局（库区-通道-货架-层-位）
- 物理库位编码自动转换为前端坐标

### 2. 热力渲染引擎
- 基于 ECharts 的热力图渲染
- 自动颜色梯度映射（0 = 浅黄，最大值 = 深红）
- 支持缩放和平移

### 3. 多维过滤器
- 时间段筛选（今天、近7天、近30天、自定义）
- 库位类型筛选（地堆、高位架等）
- 库区筛选

### 4. 数据同步接口
- RESTful API 接口
- 支持 Excel/CSV 文件上传
- 定时数据同步任务

## 热度计算公式

$$H = w_1 \cdot F + w_2 \cdot Q$$

其中：
- $H$ = 热度值
- $F$ = 拣货频率
- $Q$ = 库存周转率
- $w_1, w_2$ = 权重系数（默认 0.6, 0.4）

## 快速开始

### 使用启动程序（推荐）

双击运行 `start.bat`，会显示交互式菜单：

```
========================================
   仓库热力图系统 - 启动管理
========================================

  [1] 一键启动前后端
  [2] 仅启动后端
  [3] 仅启动前端
  [4] 停止所有服务
  [5] 初始化环境（首次使用）
  [0] 退出
```

**首次使用**请先选择 `[5] 初始化环境` 安装依赖。

### PowerShell 命令行方式

```powershell
.\scripts\Start.ps1           # 交互式菜单
.\scripts\Start.ps1 -All      # 一键启动前后端
.\scripts\Start.ps1 -Backend  # 仅启动后端
.\scripts\Start.ps1 -Frontend # 仅启动前端
.\scripts\Start.ps1 -Stop     # 停止所有服务
.\scripts\Start.ps1 -Setup    # 初始化环境
```

### 手动启动

```bash
# 后端
cd backend
pip install -r requirements.txt
python main.py

# 前端
cd frontend
npm install
npm run dev
```

### 数据库初始化

```bash
# MySQL
mysql -u root -p < database/init.sql

# PostgreSQL
psql -U postgres -f database/init.sql
```

## API 文档

启动后端后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 配置说明

### 后端配置 (backend/.env)

```env
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/warehouse_heatmap
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:5173
```

### 前端配置 (frontend/.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## License

MIT License
