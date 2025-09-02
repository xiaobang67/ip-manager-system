#!/bin/bash

# IPAM系统健康检查脚本
# 用于检查系统各组件的健康状态

set -e

# 配置变量
COMPOSE_FILE="docker-compose.prod.yml"
HEALTH_CHECK_URL="http://localhost/api/health"
GRAFANA_URL="http://localhost:3000/api/health"
PROMETHEUS_URL="http://localhost:9090/-/healthy"

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

# 检查容器状态
check_containers() {
    log_info "检查容器状态..."
    
    local containers=("ipam_nginx" "ipam_backend" "ipam_mysql" "ipam_redis" "ipam_prometheus" "ipam_grafana")
    local failed_containers=()
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")
            
            if [ "$status" = "healthy" ] || [ "$status" = "no-healthcheck" ]; then
                log_success "$container 运行正常"
            else
                log_error "$container 健康检查失败 (状态: $status)"
                failed_containers+=("$container")
            fi
        else
            log_error "$container 未运行"
            failed_containers+=("$container")
        fi
    done
    
    if [ ${#failed_containers[@]} -eq 0 ]; then
        log_success "所有容器运行正常"
        return 0
    else
        log_error "以下容器存在问题: ${failed_containers[*]}"
        return 1
    fi
}

# 检查网络连通性
check_network() {
    log_info "检查网络连通性..."
    
    local endpoints=(
        "nginx:80:Nginx Web服务器"
        "backend:8000:后端API服务"
        "mysql:3306:MySQL数据库"
        "redis:6379:Redis缓存"
        "prometheus:9090:Prometheus监控"
        "grafana:3000:Grafana仪表盘"
    )
    
    local failed_endpoints=()
    
    for endpoint in "${endpoints[@]}"; do
        IFS=':' read -r host port desc <<< "$endpoint"
        
        if timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
            log_success "$desc ($host:$port) 连接正常"
        else
            log_error "$desc ($host:$port) 连接失败"
            failed_endpoints+=("$desc")
        fi
    done
    
    if [ ${#failed_endpoints[@]} -eq 0 ]; then
        log_success "所有网络端点连接正常"
        return 0
    else
        log_error "以下端点连接失败: ${failed_endpoints[*]}"
        return 1
    fi
}

# 检查HTTP服务
check_http_services() {
    log_info "检查HTTP服务..."
    
    local services=(
        "$HEALTH_CHECK_URL:IPAM API健康检查"
        "$GRAFANA_URL:Grafana健康检查"
        "$PROMETHEUS_URL:Prometheus健康检查"
    )
    
    local failed_services=()
    
    for service in "${services[@]}"; do
        IFS=':' read -r url desc <<< "$service"
        
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10 || echo "000")
        
        if [ "$response_code" = "200" ]; then
            log_success "$desc 响应正常 (HTTP $response_code)"
        else
            log_error "$desc 响应异常 (HTTP $response_code)"
            failed_services+=("$desc")
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "所有HTTP服务响应正常"
        return 0
    else
        log_error "以下HTTP服务响应异常: ${failed_services[*]}"
        return 1
    fi
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    
    # 检查MySQL连接
    if docker-compose -f "$COMPOSE_FILE" exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1" >/dev/null 2>&1; then
        log_success "MySQL数据库连接正常"
    else
        log_error "MySQL数据库连接失败"
        return 1
    fi
    
    # 检查Redis连接
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis缓存连接正常"
    else
        log_error "Redis缓存连接失败"
        return 1
    fi
    
    return 0
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    local threshold=90
    local failed_mounts=()
    
    while IFS= read -r line; do
        local usage=$(echo "$line" | awk '{print $5}' | sed 's/%//')
        local mount=$(echo "$line" | awk '{print $6}')
        
        if [ "$usage" -gt "$threshold" ]; then
            log_error "磁盘空间不足: $mount 使用率 ${usage}%"
            failed_mounts+=("$mount")
        else
            log_success "磁盘空间正常: $mount 使用率 ${usage}%"
        fi
    done < <(df -h | grep -E '^/dev/' | grep -v '/boot')
    
    if [ ${#failed_mounts[@]} -eq 0 ]; then
        log_success "所有磁盘空间充足"
        return 0
    else
        log_error "以下挂载点磁盘空间不足: ${failed_mounts[*]}"
        return 1
    fi
}

# 检查内存使用
check_memory() {
    log_info "检查内存使用..."
    
    local total_mem=$(free | grep '^Mem:' | awk '{print $2}')
    local used_mem=$(free | grep '^Mem:' | awk '{print $3}')
    local usage=$((used_mem * 100 / total_mem))
    
    if [ "$usage" -gt 90 ]; then
        log_error "内存使用率过高: ${usage}%"
        return 1
    elif [ "$usage" -gt 80 ]; then
        log_warning "内存使用率较高: ${usage}%"
    else
        log_success "内存使用率正常: ${usage}%"
    fi
    
    return 0
}

# 检查CPU负载
check_cpu_load() {
    log_info "检查CPU负载..."
    
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local load_percentage=$(echo "scale=2; $load_avg / $cpu_cores * 100" | bc)
    
    if (( $(echo "$load_percentage > 90" | bc -l) )); then
        log_error "CPU负载过高: ${load_percentage}% (${load_avg}/${cpu_cores})"
        return 1
    elif (( $(echo "$load_percentage > 70" | bc -l) )); then
        log_warning "CPU负载较高: ${load_percentage}% (${load_avg}/${cpu_cores})"
    else
        log_success "CPU负载正常: ${load_percentage}% (${load_avg}/${cpu_cores})"
    fi
    
    return 0
}

# 检查日志错误
check_logs() {
    log_info "检查最近的错误日志..."
    
    local error_count=0
    local services=("nginx" "backend" "mysql" "redis")
    
    for service in "${services[@]}"; do
        local errors=$(docker-compose -f "$COMPOSE_FILE" logs --since="1h" "$service" 2>/dev/null | grep -i "error\|exception\|fatal" | wc -l)
        
        if [ "$errors" -gt 10 ]; then
            log_error "$service 服务在过去1小时内有 $errors 个错误"
            error_count=$((error_count + errors))
        elif [ "$errors" -gt 0 ]; then
            log_warning "$service 服务在过去1小时内有 $errors 个错误"
            error_count=$((error_count + errors))
        else
            log_success "$service 服务日志正常"
        fi
    done
    
    if [ "$error_count" -gt 50 ]; then
        log_error "系统错误日志过多，总计 $error_count 个错误"
        return 1
    elif [ "$error_count" -gt 0 ]; then
        log_warning "系统有少量错误日志，总计 $error_count 个错误"
    else
        log_success "系统日志正常，无错误记录"
    fi
    
    return 0
}

# 检查备份状态
check_backups() {
    log_info "检查备份状态..."
    
    local backup_dir="./backups"
    local latest_backup=$(find "$backup_dir" -name "mysql_backup_*.sql.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -z "$latest_backup" ]; then
        log_error "未找到数据库备份文件"
        return 1
    fi
    
    local backup_age=$(( ($(date +%s) - $(stat -c %Y "$latest_backup")) / 86400 ))
    
    if [ "$backup_age" -gt 7 ]; then
        log_error "最新备份文件过旧: $backup_age 天前 ($latest_backup)"
        return 1
    elif [ "$backup_age" -gt 1 ]; then
        log_warning "最新备份文件: $backup_age 天前 ($latest_backup)"
    else
        log_success "备份文件正常: $backup_age 天前 ($latest_backup)"
    fi
    
    return 0
}

# 生成健康报告
generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="./logs/health_check_$(date +%Y%m%d_%H%M%S).log"
    
    {
        echo "IPAM系统健康检查报告"
        echo "====================="
        echo "检查时间: $timestamp"
        echo ""
        
        echo "容器状态检查:"
        check_containers
        echo ""
        
        echo "网络连通性检查:"
        check_network
        echo ""
        
        echo "HTTP服务检查:"
        check_http_services
        echo ""
        
        echo "数据库连接检查:"
        check_database
        echo ""
        
        echo "系统资源检查:"
        check_disk_space
        check_memory
        check_cpu_load
        echo ""
        
        echo "日志错误检查:"
        check_logs
        echo ""
        
        echo "备份状态检查:"
        check_backups
        echo ""
        
        echo "检查完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    } | tee "$report_file"
    
    log_info "健康检查报告已保存到: $report_file"
}

# 主函数
main() {
    local exit_code=0
    
    echo "IPAM系统健康检查开始..."
    echo "======================"
    
    # 检查Docker和Docker Compose是否可用
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装或不可用"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装或不可用"
        exit 1
    fi
    
    # 检查环境文件
    if [ ! -f ".env.prod" ]; then
        log_error "环境配置文件 .env.prod 不存在"
        exit 1
    fi
    
    # 加载环境变量
    source .env.prod
    
    # 执行各项检查
    check_containers || exit_code=1
    echo ""
    
    check_network || exit_code=1
    echo ""
    
    check_http_services || exit_code=1
    echo ""
    
    check_database || exit_code=1
    echo ""
    
    check_disk_space || exit_code=1
    echo ""
    
    check_memory || exit_code=1
    echo ""
    
    check_cpu_load || exit_code=1
    echo ""
    
    check_logs || exit_code=1
    echo ""
    
    check_backups || exit_code=1
    echo ""
    
    # 输出总结
    if [ $exit_code -eq 0 ]; then
        log_success "所有健康检查通过！"
    else
        log_error "健康检查发现问题，请查看上述错误信息"
    fi
    
    # 根据参数决定是否生成报告
    if [ "${1:-}" = "--report" ]; then
        generate_report
    fi
    
    exit $exit_code
}

# 执行主函数
main "$@"