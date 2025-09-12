@echo off
echo ================================
echo 移除导出数据功能
echo ================================

echo.
echo 1. 停止服务...
docker-compose down

echo.
echo 2. 重新构建前端...
docker-compose build frontend

echo.
echo 3. 启动服务...
docker-compose up -d

echo.
echo 4. 等待服务启动...
timeout /t 10

echo.
echo 5. 检查服务状态...
docker-compose ps

echo.
echo ================================
echo 导出功能移除完成！
echo ================================
echo.
echo 已移除的功能：
echo - 前端IP API中的exportIPs方法
echo - 前端IP API中的importIPs方法
echo - 相关的导出/导入按钮和界面元素
echo.
echo 如果页面上仍然显示导出按钮，请：
echo 1. 清除浏览器缓存
echo 2. 强制刷新页面 (Ctrl+F5)
echo.
pause