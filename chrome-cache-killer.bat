@echo off
echo ========================================
echo Chrome 缓存终极清理器
echo ========================================

REM 1. 强制关闭Chrome
echo 1. 强制关闭Chrome进程...
taskkill /f /im chrome.exe >nul 2>&1
taskkill /f /im chromedriver.exe >nul 2>&1
timeout /t 3

REM 2. 清理Chrome所有缓存目录
echo 2. 清理Chrome缓存目录...
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\GPUCache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Service Worker" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Application Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\ShaderCache" >nul 2>&1

REM 3. 清理临时文件
echo 3. 清理系统临时文件...
del /q /f "%TEMP%\*" >nul 2>&1
for /d %%x in ("%TEMP%\*") do rd /s /q "%%x" >nul 2>&1

REM 4. 重新构建前端
echo 4. 重新构建前端...
docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d

REM 5. 等待服务启动
echo 5. 等待服务启动...
timeout /t 15

echo ========================================
echo 清理完成！现在请按以下步骤操作：
echo ========================================
echo.
echo 方法1 - 使用无痕模式（推荐）：
echo 1. 按 Ctrl+Shift+N 打开Chrome无痕窗口
echo 2. 访问 http://localhost
echo 3. 查看按钮是否变成绿色
echo.
echo 方法2 - 硬刷新：
echo 1. 打开Chrome
echo 2. 访问 http://localhost
echo 3. 按 F12 打开开发者工具
echo 4. 右键点击刷新按钮
echo 5. 选择"清空缓存并硬性重新加载"
echo.
echo 方法3 - 手动清理：
echo 1. 在Chrome中按 Ctrl+Shift+Delete
echo 2. 选择"高级"选项卡
echo 3. 时间范围选择"时间不限"
echo 4. 勾选所有选项
echo 5. 点击"清除数据"
echo.
pause

REM 6. 自动打开Chrome无痕模式
echo 正在为您打开Chrome无痕模式...
start chrome --incognito http://localhost