#!/bin/bash

# IPAM系统数据库备份脚本
# 用于定期备份MySQL数据库

set -e

# 配置变量
BACKUP_DIR="/backups"
MYSQL_HOST="mysql"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-rootpass123}"
MYSQL_DATABASE="${MYSQL_DATABASE:-ipam}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="ipam_backup_${DATE}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 创建备份目录
mkdir -p "$BACKUP_DIR"

log "开始数据库备份..."

# 执行数据库备份
mysqldump -h "$MYSQL_HOST" -u root -p"$MYSQL_ROOT_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    --all-databases > "$BACKUP_PATH"

if [ $? -eq 0 ]; then
    log "数据库备份成功: $BACKUP_FILE"
    
    # 压缩备份文件
    gzip "$BACKUP_PATH"
    log "备份文件已压缩: ${BACKUP_FILE}.gz"
    
    # 清理旧备份
    find "$BACKUP_DIR" -name "ipam_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    log "已清理 $RETENTION_DAYS 天前的旧备份文件"
    
    # 显示备份文件大小
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}.gz" | cut -f1)
    log "备份文件大小: $BACKUP_SIZE"
    
else
    log "数据库备份失败"
    exit 1
fi

log "备份任务完成"