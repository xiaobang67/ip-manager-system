@echo off
echo 正在修复Docker网络连接问题...

REM 停止现有容器
echo 停止现有容器...
docker-compose down

REM 清理Docker缓存
echo 清理Docker缓存...
docker builder prune -f
docker image prune -f
docker container prune -f

REM 配置Docker镜像源
echo 配置Docker镜像源...
if not exist "%USERPROFILE%\.docker" mkdir "%USERPROFILE%\.docker"

echo {> "%USERPROFILE%\.docker\daemon.json"
echo   "registry-mirrors": [>> "%USERPROFILE%\.docker\daemon.json"
echo     "https://docker.mirrors.ustc.edu.cn",>> "%USERPROFILE%\.docker\daemon.json"
echo     "https://hub-mirror.c.163.com",>> "%USERPROFILE%\.docker\daemon.json"
echo     "https://mirror.baidubce.com",>> "%USERPROFILE%\.docker\daemon.json"
echo     "https://ccr.ccs.tencentyun.com">> "%USERPROFILE%\.docker\daemon.json"
echo   ],>> "%USERPROFILE%\.docker\daemon.json"
echo   "insecure-registries": [],>> "%USERPROFILE%\.docker\daemon.json"
echo   "debug": false,>> "%USERPROFILE%\.docker\daemon.json"
echo   "experimental": false,>> "%USERPROFILE%\.docker\daemon.json"
echo   "features": {>> "%USERPROFILE%\.docker\daemon.json"
echo     "buildkit": true>> "%USERPROFILE%\.docker\daemon.json"
echo   }>> "%USERPROFILE%\.docker\daemon.json"
echo }>> "%USERPROFILE%\.docker\daemon.json"

echo Docker镜像源配置完成！
echo.
echo 请按以下步骤操作：
echo 1. 重启Docker Desktop
echo 2. 等待Docker完全启动
echo 3. 运行: docker-compose up --build
echo.
pause