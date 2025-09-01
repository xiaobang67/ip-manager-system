@echo off
echo ========================================
echo 企业IP地址管理系统 - 停止服务
echo ========================================
echo.

echo 停止所有服务...
docker-compose down

echo.
echo 清理未使用的镜像（可选）...
set /p cleanup="是否清理未使用的Docker镜像？(y/N): "
if /i "%cleanup%"=="y" (
    echo 清理中...
    docker image prune -f
    echo ✅ 清理完成
)

echo.
echo 服务状态：
docker-compose ps

echo.
echo ✅ 服务已停止
pause