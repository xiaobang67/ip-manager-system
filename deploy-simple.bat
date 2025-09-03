@echo off
echo ========================================
echo        IPAM 系统部署脚本
echo ========================================

echo.
echo 1. 清理旧容器...
docker-compose down

echo.
echo 2. 启动基础服务 (MySQL, Redis)...
docker-compose up -d mysql redis

echo.
echo 3. 等待数据库启动...
echo 等待 MySQL 和 Redis 完全启动...
timeout /t 15 /nobreak

echo.
echo 4. 检查服务状态...
docker-compose ps

echo.
echo 5. 测试数据库连接...
docker exec ipam_mysql mysql -u ipam_user -pipam_pass123 -e "SELECT 'Database connection successful' as status;"

echo.
echo 6. 检查数据库表...
docker exec ipam_mysql mysql -u ipam_user -pipam_pass123 ipam -e "SHOW TABLES;"

echo.
echo 7. 准备后端环境...
cd backend

echo.
echo 8. 创建 .env 文件...
echo DATABASE_URL=mysql+pymysql://ipam_user:ipam_pass123@localhost:3306/ipam > .env
echo REDIS_URL=redis://localhost:6379 >> .env
echo SECRET_KEY=your-secret-key-change-in-production >> .env
echo DEBUG=true >> .env
echo ENVIRONMENT=development >> .env

echo.
echo 9. 安装 Python 依赖...
pip install -r requirements.txt

echo.
echo 10. 启动后端服务...
echo 正在启动后端 API 服务...
start "IPAM Backend" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

cd ..

echo.
echo ========================================
echo           部署完成！
echo ========================================
echo.
echo 服务信息:
echo - MySQL: localhost:3306 (用户: ipam_user, 密码: ipam_pass123)
echo - Redis: localhost:6379
echo - 后端 API: http://localhost:8000
echo - API 文档: http://localhost:8000/docs
echo - 健康检查: http://localhost:8000/health
echo.
echo 后端服务已在新窗口中启动
echo 请等待几秒钟让服务完全启动
echo.
pause