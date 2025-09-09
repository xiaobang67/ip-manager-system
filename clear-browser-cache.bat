@echo off
echo 正在清理浏览器缓存...

REM 清理Chrome缓存
echo 清理Chrome缓存...
taskkill /f /im chrome.exe >nul 2>&1
timeout /t 2 >nul
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache" >nul 2>&1

REM 清理Edge缓存
echo 清理Edge缓存...
taskkill /f /im msedge.exe >nul 2>&1
timeout /t 2 >nul
rd /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache" >nul 2>&1

REM 清理Firefox缓存
echo 清理Firefox缓存...
taskkill /f /im firefox.exe >nul 2>&1
timeout /t 2 >nul
for /d %%x in ("%APPDATA%\Mozilla\Firefox\Profiles\*") do (
    rd /s /q "%%x\cache2" >nul 2>&1
)

echo 缓存清理完成！
echo.
echo 请按以下步骤操作：
echo 1. 打开浏览器
echo 2. 访问 http://localhost
echo 3. 按 Ctrl+F5 强制刷新页面
echo 4. 或者按 Ctrl+Shift+R 硬刷新
echo.
pause