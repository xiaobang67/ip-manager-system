@echo off
echo ================================
echo 修复用户认证切换问题
echo ================================

echo.
echo 1. 停止当前服务...
docker-compose down

echo.
echo 2. 重新构建前端镜像...
docker-compose build frontend

echo.
echo 3. 启动服务...
docker-compose up -d

echo.
echo 4. 等待服务启动...
timeout /t 10

echo.
echo 5. 检查服务状态...
docker-compose ps

echo.
echo ================================
echo 修复完成！
echo ================================
echo.
echo 修复内容：
echo - 加强了认证状态管理
echo - 添加了token与用户信息一致性检查
echo - 改进了页面刷新时的认证验证
echo - 添加了多标签页身份冲突防护
echo - 增加了定期身份验证机制
echo.
echo 测试建议：
echo 1. 清除浏览器缓存和localStorage
echo 2. 使用普通用户登录
echo 3. 按F5刷新页面，检查是否还会跳转到admin
echo 4. 在浏览器控制台运行 debugAuth.check() 检查认证数据
echo.
pause