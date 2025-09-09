@echo off
echo ========================================
echo 强制清理所有缓存 - IP管理系统
echo ========================================

REM 停止Docker服务
echo 1. 停止Docker服务...
docker-compose down

REM 清理Docker镜像缓存
echo 2. 清理Docker镜像缓存...
docker system prune -f
docker builder prune -f

REM 重新构建前端（不使用缓存）
echo 3. 重新构建前端（无缓存）...
docker-compose build --no-cache frontend

REM 启动服务
echo 4. 启动服务...
docker-compose up -d

REM 等待服务启动
echo 5. 等待服务启动...
timeout /t 10

REM 清理浏览器缓存
echo 6. 清理浏览器缓存...
taskkill /f /im chrome.exe >nul 2>&1
taskkill /f /im msedge.exe >nul 2>&1
taskkill /f /im firefox.exe >nul 2>&1
timeout /t 3

REM 清理Chrome
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\GPUCache" >nul 2>&1

REM 清理Edge
rd /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\GPUCache" >nul 2>&1

echo ========================================
echo 缓存清理完成！
echo ========================================
echo.
echo 现在请：
echo 1. 打开浏览器
echo 2. 访问 http://localhost
echo 3. 按 Ctrl+Shift+Delete 打开清理对话框
echo 4. 选择"缓存的图片和文件"
echo 5. 点击"清除数据"
echo 6. 然后按 Ctrl+F5 强制刷新页面
echo.
echo 如果还是看不到绿色按钮，请尝试：
echo - 使用无痕/隐私模式打开浏览器
echo - 或者尝试不同的浏览器
echo.
pause