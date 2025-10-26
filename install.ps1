# Academic Paper Assistant - 安装脚本

Write-Host "📦 安装 Academic Paper Assistant 依赖..." -ForegroundColor Green
Write-Host ""

# 检查 Python 版本
Write-Host "🐍 检查 Python 版本..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
Write-Host $pythonVersion

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 未找到 Python！请先安装 Python 3.8 或更高版本。" -ForegroundColor Red
    exit 1
}

# 升级 pip
Write-Host ""
Write-Host "⬆️ 升级 pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# 安装依赖
Write-Host ""
Write-Host "📥 安装项目依赖..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 依赖安装完成！" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作:" -ForegroundColor Yellow
    Write-Host "  1. 运行 '.\start.ps1' 启动服务器" -ForegroundColor White
    Write-Host "  2. 访问 http://127.0.0.1:8000/docs 查看 API 文档" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ 依赖安装失败！" -ForegroundColor Red
    Write-Host "请检查错误信息并重试。" -ForegroundColor Yellow
}
