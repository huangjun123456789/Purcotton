"""仓库热力图后端主应用"""
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db, close_db, init_default_admin
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时尝试初始化数据库（失败不影响应用启动）
    try:
        await init_db()
        print("数据库初始化完成")
        # 初始化默认管理员账户
        await init_default_admin()
    except Exception as e:
        print(f"警告: 数据库连接失败 - {e}")
        print("部分功能（如模板下载）仍可使用，但数据导入功能需要数据库连接")
    yield
    # 关闭时清理资源
    try:
        await close_db()
        print("数据库连接已关闭")
    except Exception:
        pass


# 创建 FastAPI 应用
app = FastAPI(
    title="仓库库位热力图系统",
    description="""
    ## 功能概述
    
    仓库库位热力图系统 API，用于可视化仓库库位热度数据。
    
    ### 主要功能
    
    - **仓库管理**: 创建和管理仓库、库区、通道、货架、库位
    - **热力图数据**: 获取和更新库位热度数据
    - **数据导入**: 支持 Excel/CSV 文件导入热度数据
    
    ### 热度计算公式
    
    $$H = w_1 \\cdot F + w_2 \\cdot Q$$
    
    - H = 热度值
    - F = 拣货频率
    - Q = 周转率
    - w1, w2 = 权重系数
    """,
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")

# 静态文件目录（用于部署时提供前端文件）
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


@app.get("/api-info", tags=["健康检查"])
async def api_info():
    """API 信息"""
    return {
        "status": "ok",
        "message": "仓库库位热力图系统 API",
        "version": "1.0.0"
    }


# ==================== 静态文件服务（部署时使用） ====================
# 检查静态文件目录是否存在，存在则挂载
if STATIC_DIR.exists():
    # 挂载静态资源目录（JS、CSS、图片等）
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    
    # SPA 路由回退：所有非 API 路由返回 index.html
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """服务前端 SPA 应用"""
        # API 路由不处理
        if full_path.startswith("api/"):
            return {"error": "Not found"}
        
        # 检查是否请求的是静态文件
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # 其他路由返回 index.html（SPA 路由）
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return {"error": "Frontend not built"}
else:
    # 开发模式：根路径返回 API 信息
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "status": "ok",
            "message": "仓库库位热力图系统 API（开发模式）",
            "version": "1.0.0",
            "docs": "/docs"
        }


if __name__ == "__main__":
    import uvicorn
    # 获取端口（Railway 会设置 PORT 环境变量）
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    )
