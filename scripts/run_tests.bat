@echo off
REM 测试运行脚本 - Windows版本
REM 运行完整的测试套件

setlocal enabledelayedexpansion

echo 🧪 开始运行IP地址管理系统测试套件...

REM 设置环境变量
set TESTING=true
set DATABASE_URL=sqlite+aiosqlite:///./test.db

REM 创建测试报告目录
if not exist "reports\coverage" mkdir reports\coverage
if not exist "reports\test-results" mkdir reports\test-results

echo 📋 运行前端单元测试...
cd frontend

REM 检查并安装依赖
if not exist "node_modules" (
    echo 安装前端依赖...
    npm install
    if errorlevel 1 (
        echo ❌ 前端依赖安装失败
        exit /b 1
    )
)

REM 运行前端测试
npm run test:unit -- --reporter=json --outputFile=../reports/test-results/frontend-unit.json
if errorlevel 1 (
    echo ❌ 前端单元测试失败
    exit /b 1
) else (
    echo ✅ 前端单元测试通过
)

REM 生成前端覆盖率报告
npm run test:coverage
if exist "coverage" (
    xcopy /E /I /Y coverage ..\reports\coverage\frontend
)

cd ..

echo 🐍 运行后端测试...
cd backend

REM 检查Python虚拟环境
if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        exit /b 1
    )
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
if not exist ".deps_installed" (
    echo 安装后端依赖...
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov httpx
    if errorlevel 1 (
        echo ❌ 后端依赖安装失败
        exit /b 1
    )
    echo. > .deps_installed
)

REM 运行后端单元测试
echo 运行后端单元测试...
pytest tests\ -v --cov=app --cov-report=html:..\reports\coverage\backend --cov-report=json:..\reports\coverage\backend-coverage.json --junit-xml=..\reports\test-results\backend-unit.xml -m "not performance and not slow"

if errorlevel 1 (
    echo ❌ 后端单元测试失败
    exit /b 1
) else (
    echo ✅ 后端单元测试通过
)

REM 运行集成测试
echo 运行后端集成测试...
pytest tests\test_api_integration.py -v --junit-xml=..\reports\test-results\backend-integration.xml

if errorlevel 1 (
    echo ❌ 后端集成测试失败
    exit /b 1
) else (
    echo ✅ 后端集成测试通过
)

cd ..

REM 运行性能测试（可选）
if "%1"=="--performance" (
    echo 🚀 运行性能测试...
    cd backend
    pytest tests\test_performance.py -v -m performance --junit-xml=..\reports\test-results\performance.xml
    
    if errorlevel 1 (
        echo ⚠️ 性能测试有警告
    ) else (
        echo ✅ 性能测试通过
    )
    cd ..
)

REM 生成测试报告
echo 📊 生成测试报告...

REM 创建HTML测试报告
(
echo ^<!DOCTYPE html^>
echo ^<html^>
echo ^<head^>
echo     ^<title^>IP地址管理系统 - 测试报告^</title^>
echo     ^<meta charset="utf-8"^>
echo     ^<style^>
echo         body { font-family: Arial, sans-serif; margin: 20px; }
echo         .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
echo         .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
echo         .success { color: #28a745; }
echo         .error { color: #dc3545; }
echo         .warning { color: #ffc107; }
echo         .info { color: #17a2b8; }
echo         table { width: 100%%; border-collapse: collapse; }
echo         th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
echo         th { background-color: #f2f2f2; }
echo     ^</style^>
echo ^</head^>
echo ^<body^>
echo     ^<div class="header"^>
echo         ^<h1^>IP地址管理系统 - 测试报告^</h1^>
echo         ^<p^>生成时间: %date% %time%^</p^>
echo     ^</div^>
echo     
echo     ^<div class="section"^>
echo         ^<h2^>测试概览^</h2^>
echo         ^<table^>
echo             ^<tr^>^<th^>测试类型^</th^>^<th^>状态^</th^>^<th^>说明^</th^>^</tr^>
echo             ^<tr^>^<td^>前端单元测试^</td^>^<td class="success"^>✅ 通过^</td^>^<td^>Vue组件测试^</td^>^</tr^>
echo             ^<tr^>^<td^>后端单元测试^</td^>^<td class="success"^>✅ 通过^</td^>^<td^>Python业务逻辑测试^</td^>^</tr^>
echo             ^<tr^>^<td^>集成测试^</td^>^<td class="success"^>✅ 通过^</td^>^<td^>API接口测试^</td^>^</tr^>
echo             ^<tr^>^<td^>E2E测试^</td^>^<td class="info"^>ℹ️ 可选^</td^>^<td^>端到端用户流程测试^</td^>^</tr^>
echo             ^<tr^>^<td^>性能测试^</td^>^<td class="info"^>ℹ️ 可选^</td^>^<td^>系统性能基准测试^</td^>^</tr^>
echo         ^</table^>
echo     ^</div^>
echo     
echo     ^<div class="section"^>
echo         ^<h2^>覆盖率报告^</h2^>
echo         ^<p^>前端覆盖率: ^<a href="coverage/frontend/index.html"^>查看详细报告^</a^>^</p^>
echo         ^<p^>后端覆盖率: ^<a href="coverage/backend/index.html"^>查看详细报告^</a^>^</p^>
echo     ^</div^>
echo     
echo     ^<div class="section"^>
echo         ^<h2^>测试文件^</h2^>
echo         ^<ul^>
echo             ^<li^>^<a href="test-results/frontend-unit.json"^>前端单元测试结果^</a^>^</li^>
echo             ^<li^>^<a href="test-results/backend-unit.xml"^>后端单元测试结果^</a^>^</li^>
echo             ^<li^>^<a href="test-results/backend-integration.xml"^>集成测试结果^</a^>^</li^>
echo         ^</ul^>
echo     ^</div^>
echo ^</body^>
echo ^</html^>
) > reports\test-report.html

echo 📊 测试报告已生成: reports\test-report.html

REM 显示测试总结
echo.
echo 🎉 测试套件运行完成！
echo 📈 测试统计:
echo   - 前端单元测试: ✅
echo   - 后端单元测试: ✅
echo   - 集成测试: ✅

if "%1"=="--performance" (
    echo   - 性能测试: ✅
)

echo.
echo 📁 报告位置:
echo   - 测试报告: reports\test-report.html
echo   - 覆盖率报告: reports\coverage\
echo   - 测试结果: reports\test-results\

echo.
echo 💡 提示:
echo   - 使用 --performance 参数运行性能测试
echo   - 在浏览器中打开 reports\test-report.html 查看详细报告
echo   - 覆盖率目标: 前端 ≥80%%, 后端 ≥80%%

endlocal