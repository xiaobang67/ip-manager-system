@echo off
echo ========================================
echo 添加只读角色迁移脚本
echo ========================================

cd /d "%~dp0"

echo 1. 运行只读角色数据库迁移...
python backend/add_readonly_role_migration.py
if %errorlevel% neq 0 (
    echo 迁移失败！
    pause
    exit /b 1
)

echo.
echo 2. 创建只读用户...
python backend/create_readonly_user_simple.py --username readonly --password readonly123 --email readonly@example.com
if %errorlevel% neq 0 (
    echo 创建只读用户失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 只读角色配置完成！
echo ========================================
echo.
echo 只读用户信息：
echo   用户名: readonly
echo   密码: readonly123
echo   邮箱: readonly@example.com
echo   权限: 只能查询IP地址，无法进行任何修改操作
echo.
echo 只读用户可以访问的功能：
echo   - 仪表盘
echo   - IP地址管理（仅查询和搜索）
echo   - 查看统计信息
echo.
echo 只读用户无法访问的功能：
echo   - IP分配、编辑、保留、释放、删除
echo   - 批量操作
echo   - 用户管理
echo   - 部门管理
echo   - 子网管理
echo   - 设备类型管理
echo.
pause