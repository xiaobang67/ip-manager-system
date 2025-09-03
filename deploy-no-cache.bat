@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 无缓存部署 - IP地址管理系统
echo ========================================

:: 生成构建版本号
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "BUILD_VERSION=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

echo 构建版本: %BUILD_VERSION%
echo.

echo [1/9] 停止现有服务...
docker-compose down

echo.
echo [2/9] 清理Docker缓存...
docker builder prune -f
docker system prune -f --volumes

echo.
echo [3/9] 删除旧的前端镜像...
for /f "tokens=*" %%i in ('docker images -q ipam*frontend* 2^>nul') do docker rmi %%i 2>nul

echo.
echo [4/9] 清理前端构建文件...
if exist "frontend\dist" (
    echo 删除 frontend\dist...
    rmdir /s /q "frontend\dist"
)
if exist "frontend\node_modules\.cache" (
    echo 删除 frontend\node_modules\.cache...
    rmdir /s /q "frontend\node_modules\.cache"
)

echo.
echo [5/9] 设置构建环境变量...
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1

echo.
echo [6/9] 重新构建前端（完全无缓存）...
docker-compose build --no-cache --pull frontend

echo.
echo [7/9] 重新构建后端...
docker-compose build --no-cache backend

echo.
echo [8/9] 启动所有服务...
docker-compose up -d

echo.
echo [9/9] 等待服务完全启动...
echo 检查服务状态...
timeout /t 15 /nobreak >nul

:: 检查服务状态
docker-compose ps

echo.
echo ========================================
echo 部署完成！版本: %BUILD_VERSION%
echo ========================================
echo.
echo 强制刷新浏览器缓存的方法：
echo 1. 按 Ctrl+F5 (硬刷新)
echo 2. 按 Ctrl+Shift+R (强制刷新)
echo 3. 按 F12 打开开发者工具，右键刷新按钮选择"清空缓存并硬性重新加载"
echo 4. 在浏览器地址栏输入: http://localhost/?v=%BUILD_VERSION%
echo.
echo 如果仍有缓存问题，请：
echo 1. 打开浏览器设置 ^> 隐私和安全 ^> 清除浏览数据
echo 2. 选择"缓存的图片和文件"并清除
echo 3. 或者使用无痕/隐私模式访问
echo.
echo 访问地址: http://localhost
echo API地址: http://localhost/api
echo.
pause