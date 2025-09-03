@echo off
echo 🧹 强制清理缓存并重新部署前端...

echo.
echo 1. 停止前端容器...
docker-compose down frontend

echo.
echo 2. 清理Docker构建缓存...
docker builder prune -f

echo.
echo 3. 重新构建前端（无缓存）...
docker-compose build --no-cache frontend

echo.
echo 4. 启动前端容器...
docker-compose up -d frontend

echo.
echo 5. 等待容器启动...
timeout /t 3 /nobreak > nul

echo.
echo 6. 测试前端访问...
curl -s -o nul -w "HTTP状态码: %%{http_code}" http://localhost/test-ip-management.html
echo.

echo.
echo ✅ 缓存清理完成！
echo 📱 现在可以访问: http://localhost/test-ip-management.html
echo.
pause