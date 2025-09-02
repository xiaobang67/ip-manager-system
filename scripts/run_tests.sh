#!/bin/bash

# 测试运行脚本
# 运行完整的测试套件

set -e

echo "🧪 开始运行IP地址管理系统测试套件..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 函数：检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_message $RED "错误: $1 未安装"
        exit 1
    fi
}

# 检查必要的工具
print_message $BLUE "检查必要工具..."
check_command python3
check_command npm
check_command docker

# 设置环境变量
export TESTING=true
export DATABASE_URL="sqlite+aiosqlite:///./test.db"

# 创建测试报告目录
mkdir -p reports/coverage
mkdir -p reports/test-results

print_message $BLUE "📋 运行前端单元测试..."
cd frontend

# 安装依赖
if [ ! -d "node_modules" ]; then
    print_message $YELLOW "安装前端依赖..."
    npm install
fi

# 运行前端测试
npm run test:unit -- --reporter=json --outputFile=../reports/test-results/frontend-unit.json
if [ $? -eq 0 ]; then
    print_message $GREEN "✅ 前端单元测试通过"
else
    print_message $RED "❌ 前端单元测试失败"
    exit 1
fi

# 生成前端覆盖率报告
npm run test:coverage
cp -r coverage/* ../reports/coverage/frontend/

cd ..

print_message $BLUE "🐍 运行后端测试..."
cd backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    print_message $YELLOW "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
if [ ! -f ".deps_installed" ]; then
    print_message $YELLOW "安装后端依赖..."
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov httpx
    touch .deps_installed
fi

# 运行后端单元测试
print_message $BLUE "运行后端单元测试..."
pytest tests/ -v --cov=app --cov-report=html:../reports/coverage/backend --cov-report=json:../reports/coverage/backend-coverage.json --junit-xml=../reports/test-results/backend-unit.xml -m "not performance and not slow"

if [ $? -eq 0 ]; then
    print_message $GREEN "✅ 后端单元测试通过"
else
    print_message $RED "❌ 后端单元测试失败"
    exit 1
fi

# 运行集成测试
print_message $BLUE "运行后端集成测试..."
pytest tests/test_api_integration.py -v --junit-xml=../reports/test-results/backend-integration.xml

if [ $? -eq 0 ]; then
    print_message $GREEN "✅ 后端集成测试通过"
else
    print_message $RED "❌ 后端集成测试失败"
    exit 1
fi

cd ..

# 运行性能测试（可选）
if [ "$1" = "--performance" ]; then
    print_message $BLUE "🚀 运行性能测试..."
    cd backend
    pytest tests/test_performance.py -v -m performance --junit-xml=../reports/test-results/performance.xml
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 性能测试通过"
    else
        print_message $YELLOW "⚠️  性能测试有警告"
    fi
    cd ..
fi

# 运行E2E测试（如果Cypress可用）
if command -v cypress &> /dev/null; then
    print_message $BLUE "🌐 运行E2E测试..."
    
    # 启动应用服务
    print_message $YELLOW "启动测试环境..."
    docker-compose -f docker-compose.test.yml up -d
    
    # 等待服务启动
    sleep 30
    
    cd frontend
    npx cypress run --reporter json --reporter-options "output=../reports/test-results/e2e.json"
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ E2E测试通过"
    else
        print_message $RED "❌ E2E测试失败"
    fi
    
    cd ..
    
    # 停止测试环境
    docker-compose -f docker-compose.test.yml down
else
    print_message $YELLOW "⚠️  Cypress未安装，跳过E2E测试"
fi

# 生成测试报告
print_message $BLUE "📊 生成测试报告..."

# 创建HTML测试报告
cat > reports/test-report.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>IP地址管理系统 - 测试报告</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .warning { color: #ffc107; }
        .info { color: #17a2b8; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>IP地址管理系统 - 测试报告</h1>
        <p>生成时间: $(date)</p>
    </div>
    
    <div class="section">
        <h2>测试概览</h2>
        <table>
            <tr><th>测试类型</th><th>状态</th><th>说明</th></tr>
            <tr><td>前端单元测试</td><td class="success">✅ 通过</td><td>Vue组件测试</td></tr>
            <tr><td>后端单元测试</td><td class="success">✅ 通过</td><td>Python业务逻辑测试</td></tr>
            <tr><td>集成测试</td><td class="success">✅ 通过</td><td>API接口测试</td></tr>
            <tr><td>E2E测试</td><td class="info">ℹ️ 可选</td><td>端到端用户流程测试</td></tr>
            <tr><td>性能测试</td><td class="info">ℹ️ 可选</td><td>系统性能基准测试</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>覆盖率报告</h2>
        <p>前端覆盖率: <a href="coverage/frontend/index.html">查看详细报告</a></p>
        <p>后端覆盖率: <a href="coverage/backend/index.html">查看详细报告</a></p>
    </div>
    
    <div class="section">
        <h2>测试文件</h2>
        <ul>
            <li><a href="test-results/frontend-unit.json">前端单元测试结果</a></li>
            <li><a href="test-results/backend-unit.xml">后端单元测试结果</a></li>
            <li><a href="test-results/backend-integration.xml">集成测试结果</a></li>
        </ul>
    </div>
</body>
</html>
EOF

print_message $GREEN "📊 测试报告已生成: reports/test-report.html"

# 显示测试总结
print_message $GREEN "🎉 测试套件运行完成！"
print_message $BLUE "📈 测试统计:"
echo "  - 前端单元测试: ✅"
echo "  - 后端单元测试: ✅"
echo "  - 集成测试: ✅"

if [ "$1" = "--performance" ]; then
    echo "  - 性能测试: ✅"
fi

print_message $BLUE "📁 报告位置:"
echo "  - 测试报告: reports/test-report.html"
echo "  - 覆盖率报告: reports/coverage/"
echo "  - 测试结果: reports/test-results/"

print_message $YELLOW "💡 提示:"
echo "  - 使用 --performance 参数运行性能测试"
echo "  - 在浏览器中打开 reports/test-report.html 查看详细报告"
echo "  - 覆盖率目标: 前端 ≥80%, 后端 ≥80%"