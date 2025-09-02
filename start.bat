@echo off
echo 启动IPAM系统...

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

REM 创建必要的目录
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

REM 启动服务
echo 正在启动服务...
docker-compose up --build -d

REM 等待服务启动
echo 等待服务启动...
timeout /t 30 /nobreak >nul

REM 检查服务状态
echo 检查服务状态...
docker-compose ps

echo.
echo 系统启动完成！
echo 访问地址: http://localhost
echo 查看日志: docker-compose logs -f
echo 停止服务: docker-compose down
echo.
pause