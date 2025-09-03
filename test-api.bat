@echo off
echo ========================================
echo IPAM系统API测试脚本
echo ========================================

echo.
echo 1. 测试健康检查...
curl -s http://localhost:8000/health

echo.
echo.
echo 2. 测试根端点...
curl -s http://localhost:8000/

echo.
echo.
echo 3. 测试管理员登录...
curl -s -X POST "http://localhost:8000/api/auth/login" ^
     -H "Content-Type: application/json" ^
     -d "{\"username\":\"admin\",\"password\":\"admin\"}"

echo.
echo.
echo 4. 测试manager用户登录...
curl -s -X POST "http://localhost:8000/api/auth/login" ^
     -H "Content-Type: application/json" ^
     -d "{\"username\":\"manager\",\"password\":\"password123\"}"

echo.
echo.
echo 5. 测试错误登录...
curl -s -X POST "http://localhost:8000/api/auth/login" ^
     -H "Content-Type: application/json" ^
     -d "{\"username\":\"wrong\",\"password\":\"wrong\"}"

echo.
echo.
echo 6. 测试统计信息...
curl -s http://localhost:8000/api/v1/stats

echo.
echo.
echo 7. 测试网段列表...
curl -s "http://localhost:8000/api/v1/subnets?limit=2"

echo.
echo.
echo 8. 测试IP地址列表...
curl -s "http://localhost:8000/api/v1/ip-addresses?limit=3"

echo.
echo.
echo 9. 测试前端访问...
curl -s -I http://localhost/

echo.
echo.
echo ========================================
echo 测试完成！
echo ========================================
pause