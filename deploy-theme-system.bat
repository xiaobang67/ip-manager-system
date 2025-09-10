@echo off
echo ========================================
echo 部署统一主题系统
echo ========================================

echo.
echo 1. 检查前端目录...
if not exist "frontend" (
    echo 错误: 找不到frontend目录
    pause
    exit /b 1
)

cd frontend

echo.
echo 2. 安装依赖...
call npm install

echo.
echo 3. 预览主题系统更新...
echo 正在分析需要更新的文件...
node update-theme-system.js

echo.
echo 4. 是否要应用主题系统更新？
set /p apply="输入 y 确认应用更新，或按任意键跳过: "
if /i "%apply%"=="y" (
    echo 正在应用主题系统更新...
    node update-theme-system.js --write --report
    echo 主题系统更新完成！
    echo 详细报告已保存到 theme-migration-report.json
) else (
    echo 跳过主题系统更新
)

echo.
echo 5. 构建前端应用...
call npm run build

if %errorlevel% neq 0 (
    echo 错误: 前端构建失败
    pause
    exit /b 1
)

echo.
echo 6. 重启服务...
cd ..

echo 停止现有服务...
docker-compose down

echo 启动服务...
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo 错误: 服务启动失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 统一主题系统部署完成！
echo ========================================
echo.
echo 访问地址:
echo - 主应用: http://localhost
echo - 主题测试页面: http://localhost/#/theme-test
echo.
echo 主题系统特性:
echo - 统一的CSS变量系统
echo - 自动适配明亮/暗黑主题
echo - Vue主题指令支持
echo - 响应式主题管理
echo.
echo 如需查看详细文档，请参考:
echo frontend/THEME_SYSTEM.md
echo.

pause