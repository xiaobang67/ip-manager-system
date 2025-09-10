@echo off
echo ========================================
echo 验证数据库时区设置
echo ========================================
echo.

cd backend
python verify_timezone.py

echo.
pause