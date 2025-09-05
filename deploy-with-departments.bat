@echo off
echo ========================================
echo 部署部门管理功能
echo ========================================

echo.
echo 1. 停止现有服务...
docker-compose down

echo.
echo 2. 运行数据库迁移...
cd backend
python run_migration.py
if %ERRORLEVEL% NEQ 0 (
    echo 数据库迁移失败!
    pause
    exit /b 1
)
cd ..

echo.
echo 3. 重新构建并启动服务...
docker-compose up --build -d

echo.
echo 4. 等待服务启动...
timeout /t 10 /nobreak > nul

echo.
echo 5. 检查服务状态...
docker-compose ps

echo.
echo ========================================
echo 部署完成!
echo ========================================
echo.
echo 功能说明:
echo - 用户管理: http://localhost/user-management
echo - 部门管理: http://localhost/department-management  
echo - IP地址分配现在可以选择部门
echo.
echo 默认部门已创建:
echo - 技术部 (TECH)
echo - 运维部 (OPS) 
echo - 产品部 (PRODUCT)
echo - 市场部 (MARKETING)
echo - 人事部 (HR)
echo - 财务部 (FINANCE)
echo - 客服部 (SERVICE)
echo.
pause