# 多阶段构建 Dockerfile

# 阶段1: 构建前端
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# 阶段2: 运行后端
FROM python:3.12-slim
WORKDIR /app/backend

# 安装依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 复制初始化数据库（包含仓库结构和热力值数据）
COPY backend/warehouse_heatmap_init.db ./warehouse_heatmap.db

# 从前端构建阶段复制静态文件
COPY --from=frontend-builder /app/frontend/dist ./static

# 设置环境变量
ENV PORT=8000
ENV DEBUG=false

# 暴露端口
EXPOSE 8000

# 启动命令（直接运行，WORKDIR 已设置）
CMD ["python", "main.py"]
