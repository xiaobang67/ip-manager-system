@echo off
echo ========================================
echo 时区修复脚本 - 将数据库时间调整为北京时间
echo ========================================
echo.

echo 1. 安装Python依赖...
pip install pymysql pytz

echo.
echo 2. 停止当前服务...
docker-compose down

echo.
echo 3. 执行数据库时区修复...
cd backend
python fix_timezone.py

echo.
echo 4. 更新代码中的时区使用...
python update_timezone_usage.py

echo.
echo 5. 重启Docker容器以应用新的时区设置...
cd ..
docker-compose up -d mysql
echo 等待MySQL启动...
timeout /t 15 /nobreak > nul

echo.
echo 6. 启动所有服务...
docker-compose up -d

echo.
echo 7. 验证时区设置...
timeout /t 5 /nobreak > nul
cd backend
python verify_timezone.py

echo.
echo ========================================
echo 时区修复完成！
echo ========================================
echo.
echo 修复内容:
echo - 数据库现有时间数据已调整为北京时间
echo - MySQL容器时区已设置为Asia/Shanghai
echo - 后端代码已更新使用北京时间
echo.
echo 请检查日志文件 backend/timezone_fix.log 查看详细信息
pause