@echo off
chcp 65001 >nul
echo ========================================
echo    IPAM 系统简化部署脚本
echo ========================================
echo.

REM 检查Docker是否运行
echo [1/10] 检查Docker状态...
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
echo [2/10] 创建必要的目录...
if not exist "logs" mkdir logs
if not exist "logs\nginx" mkdir logs\nginx
if not exist "logs\backend" mkdir logs\backend
if not exist "logs\mysql" mkdir logs\mysql
if not exist "logs\redis" mkdir logs\redis
if not exist "backups" mkdir backups
echo ✅ 目录创建完成

REM 检查环境配置文件
echo.
echo [3/10] 检查环境配置...
if not exist ".env" (
    echo 创建默认环境配置文件...
    echo # IPAM系统环境配置 > .env
    echo MYSQL_ROOT_PASSWORD=rootpass123 >> .env
    echo MYSQL_DATABASE=ipam >> .env
    echo MYSQL_USER=ipam_user >> .env
    echo MYSQL_PASSWORD=ipam_pass123 >> .env
    echo SECRET_KEY=ipam-secret-key-change-in-production >> .env
    echo JWT_SECRET_KEY=ipam-jwt-secret-key-change-in-production >> .env
    echo ENVIRONMENT=development >> .env
    echo DEBUG=true >> .env
    echo LOG_LEVEL=INFO >> .env
    echo ✅ 环境配置文件已创建
) else (
    echo ✅ 环境配置文件已存在
)

REM 停止现有容器
echo.
echo [4/10] 停止现有容器...
docker-compose down >nul 2>&1
echo ✅ 现有容器已停止

REM 清理Docker缓存
echo.
echo [5/10] 清理Docker缓存...
docker builder prune -f >nul 2>&1
echo ✅ 缓存清理完成

REM 拉取基础镜像
echo.
echo [6/10] 拉取基础镜像...
echo 正在拉取MySQL镜像...
docker pull mysql:8.0 >nul 2>&1
echo 正在拉取Redis镜像...
docker pull redis:6-alpine >nul 2>&1
echo ✅ 基础镜像拉取完成

REM 构建并启动服务
echo.
echo [7/10] 构建并启动服务...
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
echo [8/10] 等待服务完全启动...
echo 正在等待数据库和缓存服务启动...
timeout /t 30 /nobreak >nul
echo ✅ 服务启动等待完成

REM 检查服务状态
echo.
echo [9/10] 检查服务状态...
echo.
docker-compose ps
echo.

REM 检查服务健康状态
echo [10/10] 检查服务健康状态...
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
echo    密码: admin123
echo.

REM 询问是否打开浏览器
set /p open_browser="是否打开浏览器访问应用？(y/N): "
if /i "%open_browser%"=="y" (
    start http://localhost
)

echo.
echo 部署脚本执行完成！
pause