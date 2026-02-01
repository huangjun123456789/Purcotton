# 一键构建部署脚本
# 将前端构建并复制到后端 static 目录

param(
    [switch]$SkipFrontend,  # 跳过前端构建
    [switch]$Test           # 本地测试模式
)

$ErrorActionPreference = "Stop"
$ROOT_DIR = Split-Path -Parent $PSScriptRoot
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"
$STATIC_DIR = Join-Path $BACKEND_DIR "static"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  仓库热力图系统 - 构建部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 构建前端
if (-not $SkipFrontend) {
    Write-Host "[1/3] 构建前端..." -ForegroundColor Yellow
    
    Push-Location $FRONTEND_DIR
    try {
        # 安装依赖（如果需要）
        if (-not (Test-Path "node_modules")) {
            Write-Host "  安装前端依赖..." -ForegroundColor Gray
            npm ci
        }
        
        # 构建
        Write-Host "  执行 npm run build..." -ForegroundColor Gray
        npm run build
        
        if ($LASTEXITCODE -ne 0) {
            throw "前端构建失败"
        }
        Write-Host "  前端构建完成!" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "[1/3] 跳过前端构建" -ForegroundColor Gray
}

# 2. 复制到后端 static 目录
Write-Host "[2/3] 复制前端文件到后端..." -ForegroundColor Yellow

$DIST_DIR = Join-Path $FRONTEND_DIR "dist"
if (-not (Test-Path $DIST_DIR)) {
    throw "前端构建目录不存在: $DIST_DIR"
}

# 清理并创建 static 目录
if (Test-Path $STATIC_DIR) {
    Remove-Item -Path $STATIC_DIR -Recurse -Force
}
New-Item -ItemType Directory -Path $STATIC_DIR -Force | Out-Null

# 复制文件
Copy-Item -Path "$DIST_DIR\*" -Destination $STATIC_DIR -Recurse
Write-Host "  文件已复制到: $STATIC_DIR" -ForegroundColor Green

# 3. 本地测试或提示
if ($Test) {
    Write-Host "[3/3] 启动本地测试服务器..." -ForegroundColor Yellow
    
    Push-Location $BACKEND_DIR
    try {
        # 激活虚拟环境并启动
        if (Test-Path "venv\Scripts\Activate.ps1") {
            & ".\venv\Scripts\Activate.ps1"
        }
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  服务已启动！" -ForegroundColor Green
        Write-Host "  访问地址: http://localhost:8000" -ForegroundColor Green
        Write-Host "  API 文档: http://localhost:8000/docs" -ForegroundColor Green
        Write-Host "  按 Ctrl+C 停止服务" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        
        python main.py
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "[3/3] 构建完成!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  构建完成！下一步操作：" -ForegroundColor Green
    Write-Host "" -ForegroundColor Green
    Write-Host "  本地测试:" -ForegroundColor White
    Write-Host "    .\scripts\Build-Deploy.ps1 -Test" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Green
    Write-Host "  部署到 Railway:" -ForegroundColor White
    Write-Host "    1. 将代码推送到 GitHub" -ForegroundColor Cyan
    Write-Host "    2. 在 Railway 中连接仓库" -ForegroundColor Cyan
    Write-Host "    3. 设置环境变量后自动部署" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Green
}
