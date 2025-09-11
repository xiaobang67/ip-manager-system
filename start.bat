@echo off
chcp 65001 >nul
echo ========================================
echo        IPAM 系统快速启动
echo ========================================
echo.

REM 检查Docker是否运行
echo 检查Docker状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Docker未运行，请先启动Docker Desktop
    echo.
    pause
    exit /b 1
)
echo ✅ Docker运行正常

REM 创建必要的目录
echo.
echo 创建必要的目录...
if not exist "logs" mkdir logs
if not exist "logs\nginx" mkdir logs\nginx
if not exist "logs\backend" mkdir logs\backend
if not exist "logs\mysql" mkdir logs\mysql
if not exist "logs\redis" mkdir logs\redis
if not exist "backups" mkdir backups
echo ✅ 目录创建完成

REM 启动服务
echo.
echo 启动IPAM系统服务...
docker-compose up -d

REM 等待服务启动
echo.
echo 等待服务启动...
timeout /t 30 /nobreak >nul

REM 检查服务状态
echo.
echo 检查服务状态...
docker-compose ps

REM 简单健康检查
echo.
echo 检查服务健康状态...
timeout /t 5 /nobreak >nul

REM 检查MySQL
docker-compose exec -T mysql mysqladmin ping -h localhost -u root -prootpass123 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MySQL: 运行正常
) else (
    echo ⚠️  MySQL: 可能还在启动中
)

REM 检查Redis
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis: 运行正常
) else (
    echo ⚠️  Redis: 可能还在启动中
)

echo.
echo ========================================
echo        系统启动完成！
echo ========================================
echo.
echo 🌐 访问地址:
echo    前端应用: http://localhost
echo    后端API: http://localhost:8000
echo    API文档: http://localhost:8000/docs
echo.
echo 📝 默认登录:
echo    用户名: admin
echo    密码: admin123
echo.
echo 🔧 常用命令:
echo    查看日志: docker-compose logs -f
echo    停止服务: docker-compose down
echo    重启服务: docker-compose restart
echo.

REM 询问是否打开浏览器
set /p open_browser="是否打开浏览器访问应用？(y/N): "
if /i "%open_browser%"=="y" (
    start http://localhost
)

echo.
pause