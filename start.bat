@echo off
echo ========================================
echo 企业IP地址管理系统 - Docker部署脚本
echo ========================================
echo.

echo 检查Docker是否运行...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未启动或未安装，请先启动Docker Desktop
    pause
    exit /b 1
)
echo ✅ Docker运行正常

echo.
echo 检查Docker Compose是否可用...
docker-compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose不可用
    pause
    exit /b 1
)
echo ✅ Docker Compose可用

echo.
echo 停止现有容器（如果存在）...
docker-compose down

echo.
echo 构建并启动服务...
docker-compose up --build -d

echo.
echo 等待服务启动...
timeout /t 30 /nobreak >nul

echo.
echo 检查服务状态...
docker-compose ps

echo.
echo ========================================
echo 🎉 部署完成！
echo ========================================
echo.
echo 📊 访问地址：
echo   前端系统: http://localhost
echo   后端API:  http://localhost:8000
echo   API文档:  http://localhost:8000/docs
echo.
echo 📋 默认数据库信息：
echo   主机: localhost:3306
echo   数据库: ip_management_system
echo   用户名: ipuser
echo   密码: ippassword
echo.
echo 🔧 管理命令：
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.
echo 按任意键打开浏览器...
pause >nul
start http://localhost