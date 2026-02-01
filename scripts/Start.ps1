# 仓库热力图系统 - 统一启动脚本
# 用法: 
#   .\scripts\Start.ps1           # 交互式菜单
#   .\scripts\Start.ps1 -All      # 启动全部
#   .\scripts\Start.ps1 -Backend  # 仅后端
#   .\scripts\Start.ps1 -Frontend # 仅前端
#   .\scripts\Start.ps1 -Stop     # 停止服务
#   .\scripts\Start.ps1 -Setup    # 初始化环境

param(
    [switch]$All,
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$Stop,
    [switch]$Setup
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 获取本机局域网 IP
$LocalIP = (Get-NetIPAddress -AddressFamily IPv4 | 
    Where-Object { $_.IPAddress -match '^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)' } | 
    Select-Object -First 1).IPAddress
if (-not $LocalIP) { $LocalIP = "未检测到" }

function Write-Color($Message, $Color = "White") {
    Write-Host $Message -ForegroundColor $Color
}

function Show-Header($Title) {
    Write-Color "`n========================================" "Cyan"
    Write-Color "   $Title" "Cyan"
    Write-Color "========================================`n" "Cyan"
}

function Start-BackendService {
    Write-Color "[INFO] 启动后端服务..." "Yellow"
    
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$ProjectRoot\backend'; " +
        "if (Test-Path '.\venv\Scripts\Activate.ps1') { & '.\venv\Scripts\Activate.ps1' }; " +
        "`$Host.UI.RawUI.WindowTitle = '后端服务 - 仓库热力图'; " +
        "Write-Host '本机访问: http://localhost:8000' -ForegroundColor Cyan; " +
        "Write-Host '局域网:   http://${LocalIP}:8000' -ForegroundColor Cyan; " +
        "Write-Host 'API文档:  http://localhost:8000/docs' -ForegroundColor Cyan; " +
        "python main.py"
    )
    
    Write-Color "[OK] 后端已启动" "Green"
    Write-Color "   本机: http://localhost:8000" "White"
    Write-Color "   局域网: http://${LocalIP}:8000" "White"
}

function Start-FrontendService {
    Write-Color "[INFO] 启动前端服务..." "Yellow"
    
    # 检查 node_modules
    if (-not (Test-Path "$ProjectRoot\frontend\node_modules")) {
        Write-Color "[WARN] 安装前端依赖..." "Yellow"
        Push-Location "$ProjectRoot\frontend"
        npm install
        Pop-Location
    }
    
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$ProjectRoot\frontend'; " +
        "`$Host.UI.RawUI.WindowTitle = '前端服务 - 仓库热力图'; " +
        "Write-Host '本机访问: http://localhost:5173' -ForegroundColor Cyan; " +
        "Write-Host '局域网:   http://${LocalIP}:5173' -ForegroundColor Cyan; " +
        "npm run dev"
    )
    
    Write-Color "[OK] 前端已启动" "Green"
    Write-Color "   本机: http://localhost:5173" "White"
    Write-Color "   局域网: http://${LocalIP}:5173" "White"
}

function Stop-AllServices {
    Show-Header "停止所有服务"
    
    # 停止后端
    $backend = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($backend) {
        $backend | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
        Write-Color "[OK] 后端服务已停止" "Green"
    } else {
        Write-Color "[--] 后端服务未运行" "Gray"
    }
    
    # 停止前端
    $frontend = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
    if ($frontend) {
        $frontend | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
        Write-Color "[OK] 前端服务已停止" "Green"
    } else {
        Write-Color "[--] 前端服务未运行" "Gray"
    }
}

function Initialize-Environment {
    Show-Header "初始化开发环境"
    
    # 检查依赖
    Write-Color "[检查] Python: $(python --version 2>&1)" "White"
    Write-Color "[检查] Node.js: $(node --version 2>&1)" "White"
    Write-Color "[检查] npm: $(npm --version 2>&1)" "White"
    
    # 后端环境
    Write-Color "`n[后端] 配置 Python 环境..." "Yellow"
    Push-Location "$ProjectRoot\backend"
    
    if (-not (Test-Path "venv")) {
        Write-Color "   创建虚拟环境..." "White"
        python -m venv venv
    }
    
    & ".\venv\Scripts\Activate.ps1"
    Write-Color "   安装依赖..." "White"
    pip install -r requirements.txt -q
    
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Copy-Item ".env.example" ".env"
        Write-Color "   [WARN] 已创建 .env，请配置数据库连接" "Yellow"
    }
    Pop-Location
    
    # 前端环境
    Write-Color "`n[前端] 配置 Node.js 环境..." "Yellow"
    Push-Location "$ProjectRoot\frontend"
    npm install
    Pop-Location
    
    Write-Color "`n[SUCCESS] 环境初始化完成！" "Green"
}

function Show-Menu {
    while ($true) {
        Clear-Host
        Show-Header "仓库热力图系统 - 启动管理"
        
        Write-Color "  本机 IP: $LocalIP`n" "Yellow"
        Write-Color "  [1] 一键启动前后端" "White"
        Write-Color "  [2] 仅启动后端" "White"
        Write-Color "  [3] 仅启动前端" "White"
        Write-Color "  [4] 停止所有服务" "White"
        Write-Color "  [5] 初始化环境" "White"
        Write-Color "  [0] 退出`n" "White"
        
        $choice = Read-Host "请选择操作 [0-5]"
        
        switch ($choice) {
            "1" {
                Show-Header "启动前后端服务"
                Start-BackendService
                Start-Sleep -Seconds 2
                Start-FrontendService
                Write-Color "`n按任意键返回菜单..." "Gray"
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "2" {
                Show-Header "启动后端服务"
                Start-BackendService
                Write-Color "`n按任意键返回菜单..." "Gray"
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "3" {
                Show-Header "启动前端服务"
                Start-FrontendService
                Write-Color "`n按任意键返回菜单..." "Gray"
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "4" {
                Stop-AllServices
                Write-Color "`n按任意键返回菜单..." "Gray"
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "5" {
                Initialize-Environment
                Write-Color "`n按任意键返回菜单..." "Gray"
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "0" { return }
        }
    }
}

# 主逻辑
if ($Setup) {
    Initialize-Environment
} elseif ($Stop) {
    Stop-AllServices
} elseif ($All) {
    Show-Header "启动前后端服务"
    Start-BackendService
    Start-Sleep -Seconds 2
    Start-FrontendService
    Write-Color "`n服务启动完成！" "Green"
} elseif ($Backend) {
    Show-Header "启动后端服务"
    Start-BackendService
} elseif ($Frontend) {
    Show-Header "启动前端服务"
    Start-FrontendService
} else {
    Show-Menu
}
