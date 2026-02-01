"""API 路由模块"""
from fastapi import APIRouter
from app.api.warehouse import router as warehouse_router
from app.api.heatmap import router as heatmap_router
from app.api.import_data import router as import_router
from app.api.report import router as report_router
from app.api.auth import router as auth_router
from app.api.user import router as user_router

api_router = APIRouter()

# 认证相关
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(user_router, prefix="/users", tags=["用户管理"])

# 业务功能
api_router.include_router(warehouse_router, prefix="/warehouse", tags=["仓库管理"])
api_router.include_router(heatmap_router, prefix="/heatmap", tags=["热力图"])
api_router.include_router(import_router, prefix="/import", tags=["数据导入"])
api_router.include_router(report_router, prefix="/report", tags=["分析报告"])
