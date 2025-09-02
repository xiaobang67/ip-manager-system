#!/bin/bash

# Docker网络问题修复脚本
# 解决Docker Hub连接问题

set -e

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

# 检查操作系统
check_os() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "linux"
    fi
}

# 配置Docker镜像源 - Windows
configure_docker_windows() {
    log_info "配置Windows Docker Desktop镜像源..."
    
    local docker_config_dir="$HOME/.docker"
    local daemon_json="$docker_config_dir/daemon.json"
    
    # 创建配置目录
    mkdir -p "$docker_config_dir"
    
    # 备份现有配置
    if [ -f "$daemon_json" ]; then
        cp "$daemon_json" "$daemon_json.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置到 $daemon_json.backup.*"
    fi
    
    # 写入新配置
    cat > "$daemon_json" << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false,
  "features": {
    "buildkit": true
  }
}
EOF
    
    log_success "Docker镜像源配置完成"
    log_warning "请重启Docker Desktop以使配置生效"
}

# 配置Docker镜像源 - Linux/macOS
configure_docker_unix() {
    log_info "配置Docker镜像源..."
    
    local daemon_json="/etc/docker/daemon.json"
    
    # 检查是否有sudo权限
    if ! sudo -n true 2>/dev/null; then
        log_error "需要sudo权限来配置Docker"
        return 1
    fi
    
    # 创建配置目录
    sudo mkdir -p /etc/docker
    
    # 备份现有配置
    if [ -f "$daemon_json" ]; then
        sudo cp "$daemon_json" "$daemon_json.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置"
    fi
    
    # 写入新配置
    sudo tee "$daemon_json" > /dev/null << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false,
  "features": {
    "buildkit": true
  }
}
EOF
    
    log_success "Docker镜像源配置完成"
    
    # 重启Docker服务
    log_info "重启Docker服务..."
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    
    log_success "Docker服务已重启"
}

# 测试Docker连接
test_docker_connection() {
    log_info "测试Docker连接..."
    
    # 测试拉取小镜像
    if docker pull hello-world:latest; then
        log_success "Docker连接测试成功"
        return 0
    else
        log_error "Docker连接测试失败"
        return 1
    fi
}

# 清理Docker缓存
clean_docker_cache() {
    log_info "清理Docker缓存..."
    
    # 清理构建缓存
    docker builder prune -f
    
    # 清理未使用的镜像
    docker image prune -f
    
    # 清理未使用的容器
    docker container prune -f
    
    log_success "Docker缓存清理完成"
}

# 预拉取必要镜像
pull_required_images() {
    log_info "预拉取必要镜像..."
    
    local images=(
        "nginx:alpine"
        "mysql:8.0"
        "redis:6-alpine"
        "node:16-alpine"
        "python:3.9-slim"
        "prom/prometheus:latest"
        "grafana/grafana:latest"
    )
    
    for image in "${images[@]}"; do
        log_info "拉取镜像: $image"
        if docker pull "$image"; then
            log_success "成功拉取: $image"
        else
            log_error "拉取失败: $image"
        fi
    done
}

# 主函数
main() {
    log_info "开始修复Docker网络问题..."
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker未运行，请启动Docker"
        exit 1
    fi
    
    # 根据操作系统配置镜像源
    local os_type=$(check_os)
    case $os_type in
        "windows")
            configure_docker_windows
            ;;
        "linux"|"macos")
            configure_docker_unix
            ;;
        *)
            log_error "不支持的操作系统: $os_type"
            exit 1
            ;;
    esac
    
    # 清理缓存
    clean_docker_cache
    
    # 等待Docker重启（如果需要）
    if [ "$os_type" != "windows" ]; then
        log_info "等待Docker服务重启..."
        sleep 10
    else
        log_warning "请手动重启Docker Desktop，然后按回车继续..."
        read -r
    fi
    
    # 测试连接
    if test_docker_connection; then
        log_success "Docker网络问题修复成功！"
        
        # 询问是否预拉取镜像
        echo ""
        log_info "是否预拉取项目所需镜像？(y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            pull_required_images
        fi
    else
        log_error "Docker网络问题修复失败，请检查网络连接"
        exit 1
    fi
    
    echo ""
    log_success "修复完成！现在可以重新运行部署命令"
}

# 执行主函数
main "$@"