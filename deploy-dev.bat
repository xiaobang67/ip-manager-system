@echo off
chcp 65001 >nul
echo ========================================
echo    IPAM系统开发环境部署脚本
echo ========================================
echo.

REM 检查Docker是否运行
echo [1/8] 检查Docker状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Docker未运行，请先启动Docker Desktop
    echo.
    echo 请按以下步骤操作：
    echo 1. 启动Docker Desktop
    echo 2. 等待Docker完全启动
    echo 3. 重新运行此脚本
    pause
    exit /b 1
)
echo ✅ Docker运行正常

REM 创建必要的目录
echo.
echo [2/8] 创建必要的目录...
if not exist "logs" mkdir logs
if not exist "logs\nginx" mkdir logs\nginx
if not exist "logs\backend" mkdir logs\backend
if not exist "logs\mysql" mkdir logs\mysql
if not exist "logs\redis" mkdir logs\redis
if not exist "backups" mkdir backups
echo ✅ 目录创建完成

REM 停止现有容器
echo.
echo [3/8] 停止现有容器...
docker-compose down >nul 2>&1
echo ✅ 现有容器已停止

REM 清理Docker缓存
echo.
echo [4/8] 清理Docker缓存...
docker builder prune -f >nul 2>&1
echo ✅ 缓存清理完成

REM 拉取基础镜像
echo.
echo [5/8] 拉取基础镜像...
echo 正在拉取MySQL镜像...
docker pull registry.cn-hangzhou.aliyuncs.com/library/mysql:8.0
echo 正在拉取Redis镜像...
docker pull registry.cn-hangzhou.aliyuncs.com/library/redis:6-alpine
echo ✅ 基础镜像拉取完成

REM 构建并启动服务
echo.
echo [6/8] 构建并启动服务...
echo 这可能需要几分钟时间，请耐心等待...
docker-compose up --build -d
if %errorlevel% neq 0 (
    echo ❌ 服务启动失败，请检查错误信息
    echo.
    echo 查看详细日志: docker-compose logs
    pause
    exit /b 1
)
echo ✅ 服务构建和启动完成

REM 等待服务启动
echo.
echo [7/8] 等待服务完全启动...
timeout /t 30 /nobreak >nul
echo ✅ 服务启动等待完成

REM 检查服务状态
echo.
echo [8/8] 检查服务状态...
echo.
docker-compose ps
echo.

REM 检查服务健康状态
echo 检查服务健康状态...
echo.

REM 检查MySQL
docker-compose exec -T mysql mysqladmin ping -h localhost -u root -prootpass123 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MySQL: 运行正常
) else (
    echo ❌ MySQL: 连接失败
)

REM 检查Redis
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis: 运行正常
) else (
    echo ❌ Redis: 连接失败
)

REM 检查后端API
timeout /t 5 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端API: 运行正常
) else (
    echo ⚠️  后端API: 可能还在启动中
)

REM 检查前端
curl -s http://localhost >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 前端: 运行正常
) else (
    echo ⚠️  前端: 可能还在启动中
)

echo.
echo ========================================
echo           部署完成！
echo ========================================
echo.
echo 🌐 访问地址:
echo    前端应用: http://localhost
echo    后端API: http://localhost:8000
echo    API文档: http://localhost:8000/docs
echo.
echo 📊 数据库信息:
echo    MySQL: localhost:3306
echo    用户名: ipam_user
echo    密码: ipam_pass123
echo    数据库: ipam
echo.
echo 🔧 常用命令:
echo    查看日志: docker-compose logs -f
echo    停止服务: docker-compose down
echo    重启服务: docker-compose restart
echo    进入容器: docker-compose exec [service] bash
echo.
echo 📝 默认登录信息:
echo    用户名: admin
echo    密码: password123
echo.

REM 询问是否打开浏览器
set /p open_browser="是否打开浏览器访问应用？(y/N): "
if /i "%open_browser%"=="y" (
    start http://localhost
)

echo.
echo 部署脚本执行完成！
pause