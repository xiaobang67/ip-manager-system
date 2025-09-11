@echo off
echo 正在运行数据库迁移...
cd backend
python run_migration.py
if %ERRORLEVEL% EQU 0 (
    echo 数据库迁移成功完成!
) else (
    echo 数据库迁移失败!
    pause
)
cd ..