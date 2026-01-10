# FFmpeg 自动安装脚本
# 使用方法：在 PowerShell 中运行 .\install_ffmpeg.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FFmpeg 安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已安装
Write-Host "检查 FFmpeg 是否已安装..." -ForegroundColor Yellow
try {
    $version = ffmpeg -version 2>$null
    if ($?) {
        Write-Host "✓ FFmpeg 已安装！" -ForegroundColor Green
        ffmpeg -version | Select-Object -First 3
        Write-Host ""
        Write-Host "无需重新安装。" -ForegroundColor Green
        exit 0
    }
} catch {
    Write-Host "✗ FFmpeg 未安装，开始安装..." -ForegroundColor Red
}

Write-Host ""
Write-Host "请选择安装方式：" -ForegroundColor Cyan
Write-Host "1. 使用 Chocolatey（推荐，最快）" -ForegroundColor White
Write-Host "2. 使用 Scoop（轻量级）" -ForegroundColor White
Write-Host "3. 手动下载安装（无需包管理器）" -ForegroundColor White
Write-Host "4. 取消" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "检查 Chocolatey..." -ForegroundColor Yellow

        # 检查 Chocolatey 是否已安装
        try {
            choco --version 2>$null | Out-Null
            Write-Host "✓ Chocolatey 已安装" -ForegroundColor Green
        } catch {
            Write-Host "✗ Chocolatey 未安装，正在安装..." -ForegroundColor Red
            Write-Host "请以管理员身份运行此脚本！" -ForegroundColor Red
            Write-Host ""
            Write-Host "或者手动安装 Chocolatey：" -ForegroundColor Yellow
            Write-Host "1. 以管理员身份打开 PowerShell" -ForegroundColor White
            Write-Host "2. 运行以下命令：" -ForegroundColor White
            Write-Host "   Set-ExecutionPolicy Bypass -Scope Process -Force" -ForegroundColor Cyan
            Write-Host "   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072" -ForegroundColor Cyan
            Write-Host "   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" -ForegroundColor Cyan
            Write-Host ""
            Read-Host "按 Enter 键退出"
            exit 1
        }

        Write-Host ""
        Write-Host "正在安装 FFmpeg..." -ForegroundColor Yellow
        choco install ffmpeg -y

        Write-Host ""
        Write-Host "安装完成！请重新打开 PowerShell 或命令提示符。" -ForegroundColor Green
    }

    "2" {
        Write-Host ""
        Write-Host "检查 Scoop..." -ForegroundColor Yellow

        # 检查 Scoop 是否已安装
        try {
            scoop --version 2>$null | Out-Null
            Write-Host "✓ Scoop 已安装" -ForegroundColor Green
        } catch {
            Write-Host "✗ Scoop 未安装，正在安装..." -ForegroundColor Red
            Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
            irm get.scoop.sh | iex
        }

        Write-Host ""
        Write-Host "正在安装 FFmpeg..." -ForegroundColor Yellow
        scoop install ffmpeg

        Write-Host ""
        Write-Host "安装完成！请重新打开 PowerShell。" -ForegroundColor Green
    }

    "3" {
        Write-Host ""
        Write-Host "手动安装步骤：" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. 下载 FFmpeg：" -ForegroundColor White
        Write-Host "   访问：https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Cyan
        Write-Host "   下载：ffmpeg-release-essentials.zip" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "2. 解压到：C:\ffmpeg" -ForegroundColor White
        Write-Host ""
        Write-Host "3. 添加到环境变量：" -ForegroundColor White
        Write-Host "   - 按 Win+R，输入：sysdm.cpl" -ForegroundColor Cyan
        Write-Host "   - 高级 → 环境变量" -ForegroundColor Cyan
        Write-Host "   - 系统变量 → Path → 新建" -ForegroundColor Cyan
        Write-Host "   - 添加：C:\ffmpeg\bin" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "4. 重新打开 PowerShell 并验证：" -ForegroundColor White
        Write-Host "   ffmpeg -version" -ForegroundColor Cyan
        Write-Host ""
    }

    "4" {
        Write-Host "已取消安装。" -ForegroundColor Yellow
        exit 0
    }

    default {
        Write-Host "无效的选项。" -ForegroundColor Red
    }
}

Write-Host ""
Read-Host "按 Enter 键退出"
