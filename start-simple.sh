#!/bin/bash

# IPAM系统简化启动脚本 - 兼容老版本Docker Compose
# 适用于 Docker Compose 1.x 和 2.x 版本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker
check_docker() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
    
    # 检查Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        log_info "使用 docker-compose 命令"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        log_info "使用 docker compose 命令"
    else
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    directories=(
        "logs/mysql"
        "logs/redis" 
        "logs/backend"
        "logs/nginx"
        "backups"
        "database"
        "nginx/ssl"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
    
    # 设置权限
    chmod -R 755 logs/ backups/ 2>/dev/null || true
    
    log_success "目录创建完成"
}

# 检查环境变量文件
check_env_file() {
    log_info "检查环境变量配置..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning ".env文件不存在，从.env.example复制"
            cp .env.example .env
        else
            log_warning ".env文件不存在，使用默认配置"
            cat > .env << 'EOF'
# IPAM系统环境配置
MYSQL_ROOT_PASSWORD=root_pass123
MYSQL_DATABASE=ipam
MYSQL_USER=ipam_user
MYSQL_PASSWORD=ipam_pass123
MYSQL_PORT=3306
REDIS_PORT=6379
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRE_MINUTES=30
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
FRONTEND_PORT=80
FRONTEND_HTTPS_PORT=443
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost,http://localhost:3000,http://localhost:5173
EOF
        fi
    fi
    
    log_success "环境变量文件检查完成"
}

# 验证配置文件
validate_config() {
    log_info "验证Docker Compose配置..."
    
    if ! $COMPOSE_CMD config > /dev/null 2>&1; then
        log_error "Docker Compose配置文件有错误"
        $COMPOSE_CMD config
        exit 1
    fi
    
    log_success "配置文件验证通过"
}

# 停止现有容器
stop_containers() {
    log_info "停止现有容器..."
    
    if $COMPOSE_CMD ps -q 2>/dev/null | grep -q .; then
        $COMPOSE_CMD down
        log_success "现有容器已停止"
    else
        log_info "没有运行中的容器"
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 拉取镜像
    log_info "拉取Docker镜像..."
    $COMPOSE_CMD pull 2>/dev/null || log_warning "部分镜像拉取失败，将使用本地镜像"
    
    # 启动服务
    log_info "启动所有服务..."
    $COMPOSE_CMD up -d
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待MySQL
    log_info "等待MySQL启动..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if $COMPOSE_CMD exec -T mysql mysqladmin ping -h localhost -u root -proot_pass123 &> /dev/null; then
            log_success "MySQL: 运行正常"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
        echo -n "."
    done
    echo ""
    
    if [ $timeout -le 0 ]; then
        log_warning "MySQL启动超时，但服务可能仍在启动中"
    fi
    
    # 等待Redis
    log_info "等待Redis启动..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if $COMPOSE_CMD exec -T redis redis-cli ping &> /dev/null; then
            log_success "Redis: 运行正常"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
        echo -n "."
    done
    echo ""
    
    if [ $timeout -le 0 ]; then
        log_warning "Redis启动超时，但服务可能仍在启动中"
    fi
    
    # 简单等待其他服务
    log_info "等待其他服务启动..."
    sleep 10
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    $COMPOSE_CMD ps
    
    echo ""
    log_info "访问地址:"
    echo "  前端应用: http://localhost"
    echo "  后端API: http://localhost:8000"
    echo ""
    
    log_info "常用命令:"
    echo "  查看日志: $COMPOSE_CMD logs -f"
    echo "  重启服务: $COMPOSE_CMD restart"
    echo "  停止服务: $COMPOSE_CMD down"
}

# 主函数
main() {
    echo "========================================"
    echo "    IPAM系统简化启动脚本"
    echo "========================================"
    echo ""
    
    check_docker
    create_directories
    check_env_file
    validate_config
    stop_containers
    start_services
    wait_for_services
    show_status
    
    echo ""
    log_success "IPAM系统启动完成！"
    echo ""
}

# 执行主函数
main "$@"