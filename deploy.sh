#!/bin/bash

# IPAM系统生产环境部署脚本
# 使用方法: ./deploy.sh [start|stop|restart|update|logs|status]

set -e

# 配置变量
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# 颜色输出
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

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 检查环境文件
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "环境配置文件 $ENV_FILE 不存在，正在创建模板..."
        create_env_template
        log_error "请编辑 $ENV_FILE 文件并设置正确的配置值"
        exit 1
    fi
}

# 创建环境配置模板
create_env_template() {
    cat > "$ENV_FILE" << EOF
# MySQL配置
MYSQL_ROOT_PASSWORD=your_strong_root_password
MYSQL_PASSWORD=your_strong_password

# JWT配置
JWT_SECRET_KEY=your_jwt_secret_key_here

# CORS配置
CORS_ORIGINS=http://localhost,https://yourdomain.com

# Grafana配置
GRAFANA_PASSWORD=your_grafana_password

# 备份配置
BACKUP_RETENTION_DAYS=30

# 监控配置
ALERT_EMAIL=admin@yourdomain.com
EOF
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p "$LOG_DIR"/{nginx,backend,mysql,redis}
    mkdir -p "$BACKUP_DIR"
    mkdir -p ./nginx/ssl
    mkdir -p ./mysql
    mkdir -p ./redis
    mkdir -p ./monitoring/{grafana/{dashboards,datasources},prometheus}
    
    log_success "目录创建完成"
}

# 生成SSL证书（自签名，生产环境建议使用Let's Encrypt）
generate_ssl_cert() {
    if [ ! -f "./nginx/ssl/server.crt" ]; then
        log_info "生成SSL证书..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ./nginx/ssl/server.key \
            -out ./nginx/ssl/server.crt \
            -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
        
        log_success "SSL证书生成完成"
    fi
}

# 数据库备份
backup_database() {
    log_info "开始数据库备份..."
    
    BACKUP_FILE="$BACKUP_DIR/mysql_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    docker-compose -f "$COMPOSE_FILE" exec -T mysql mysqldump \
        -u root -p"$MYSQL_ROOT_PASSWORD" \
        --all-databases --routines --triggers > "$BACKUP_FILE"
    
    # 压缩备份文件
    gzip "$BACKUP_FILE"
    
    log_success "数据库备份完成: ${BACKUP_FILE}.gz"
    
    # 清理旧备份
    find "$BACKUP_DIR" -name "mysql_backup_*.sql.gz" -mtime +${BACKUP_RETENTION_DAYS:-30} -delete
}

# 启动服务
start_services() {
    log_info "启动IPAM系统..."
    
    check_dependencies
    check_env_file
    create_directories
    generate_ssl_cert
    
    # 拉取最新镜像
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # 构建并启动服务
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    check_services_health
    
    log_success "IPAM系统启动完成"
    log_info "访问地址: http://localhost (HTTP) 或 https://localhost (HTTPS)"
    log_info "Grafana监控: http://localhost:3000"
    log_info "Prometheus: http://localhost:9090"
}

# 停止服务
stop_services() {
    log_info "停止IPAM系统..."
    
    # 备份数据库
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q mysql; then
        backup_database
    fi
    
    # 停止服务
    docker-compose -f "$COMPOSE_FILE" down
    
    log_success "IPAM系统已停止"
}

# 重启服务
restart_services() {
    log_info "重启IPAM系统..."
    stop_services
    start_services
}

# 更新系统
update_system() {
    log_info "更新IPAM系统..."
    
    # 备份数据库
    backup_database
    
    # 拉取最新代码（如果使用Git）
    if [ -d ".git" ]; then
        git pull
    fi
    
    # 重新构建并启动
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    log_success "系统更新完成"
}

# 查看日志
view_logs() {
    if [ -n "$2" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f "$2"
    else
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# 检查服务健康状态
check_services_health() {
    log_info "检查服务健康状态..."
    
    services=("nginx" "backend" "mysql" "redis")
    
    for service in "${services[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "$service.*Up"; then
            log_success "$service 服务运行正常"
        else
            log_error "$service 服务异常"
        fi
    done
    
    # 检查HTTP响应
    if curl -f -s http://localhost/health > /dev/null; then
        log_success "HTTP健康检查通过"
    else
        log_warning "HTTP健康检查失败"
    fi
}

# 显示服务状态
show_status() {
    log_info "IPAM系统服务状态:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    check_services_health
    
    echo ""
    log_info "磁盘使用情况:"
    docker system df
    
    echo ""
    log_info "容器资源使用:"
    docker stats --no-stream
}

# 清理系统
cleanup_system() {
    log_warning "这将删除所有未使用的Docker资源，是否继续? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        docker system prune -f
        docker volume prune -f
        log_success "系统清理完成"
    else
        log_info "取消清理操作"
    fi
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        update)
            update_system
            ;;
        logs)
            view_logs "$@"
            ;;
        status)
            show_status
            ;;
        backup)
            backup_database
            ;;
        cleanup)
            cleanup_system
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|update|logs|status|backup|cleanup}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动IPAM系统"
            echo "  stop    - 停止IPAM系统"
            echo "  restart - 重启IPAM系统"
            echo "  update  - 更新IPAM系统"
            echo "  logs    - 查看日志 (可指定服务名)"
            echo "  status  - 显示服务状态"
            echo "  backup  - 手动备份数据库"
            echo "  cleanup - 清理Docker资源"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"