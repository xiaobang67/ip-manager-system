@echo off
echo ================================
echo 测试认证修复效果
echo ================================

echo.
echo 1. 重新构建并启动服务...
docker-compose down
docker-compose build frontend
docker-compose up -d

echo.
echo 2. 等待服务启动...
timeout /t 15

echo.
echo 3. 检查服务状态...
docker-compose ps

echo.
echo ================================
echo 测试步骤：
echo ================================
echo.
echo 1. 打开浏览器访问系统
echo 2. 清除浏览器缓存和localStorage（F12 -> Application -> Storage -> Clear storage）
echo 3. 使用普通用户登录（如：user1/password）
echo 4. 登录成功后，按F5刷新页面
echo 5. 检查是否还会跳转到登录页
echo.
echo 如果仍有问题，请在浏览器控制台运行：
echo debugAuth.check()
echo.
echo 预期结果：
echo - 普通用户刷新页面应该保持登录状态
echo - 不应该跳转到登录页
echo - 用户信息应该保持一致
echo.
pause