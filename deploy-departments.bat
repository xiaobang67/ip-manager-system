@echo off
echo ========================================
echo 部门管理功能部署脚本
echo ========================================

echo.
echo 1. 停止现有服务...
docker-compose down

echo.
echo 2. 清理Docker缓存...
docker system prune -f

echo.
echo 3. 重新构建并启动服务...
docker-compose up -d --build

echo.
echo 4. 等待服务启动...
timeout /t 30 /nobreak

echo.
echo 5. 初始化部门表...
docker-compose exec backend python init_departments.py

echo.
echo 6. 检查服务状态...
docker-compose ps

echo.
echo 7. 显示后端日志（最后20行）...
docker-compose logs --tail=20 backend

echo.
echo ========================================
echo 部门管理功能部署完成！
echo ========================================
echo.
echo 访问地址: http://localhost
echo 管理员账号: admin / admin
echo.
echo 如果遇到问题，请检查：
echo 1. 数据库连接是否正常
echo 2. 部门表是否创建成功
echo 3. API路由是否正确注册
echo.
pause