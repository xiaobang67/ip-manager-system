"""
数据库种子数据脚本
用于初始化系统默认数据，包括默认admin用户和系统配置
"""

import logging
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime
from typing import Optional

from app.core.database import get_db_session, SessionLocal
from app.models.user import User, UserRole, UserTheme
from app.models.system_config import SystemConfig
from app.models.tag import Tag

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)


def create_default_admin_user(db: Session) -> Optional[User]:
    """
    创建默认的admin用户
    
    Args:
        db: 数据库会话
        
    Returns:
        User: 创建的用户对象，如果已存在则返回None
    """
    try:
        # 检查是否已存在admin用户
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            logger.info("Default admin user already exists")
            return None
        
        # 创建默认admin用户
        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),  # 默认密码，生产环境需要修改
            email="admin@ipam.local",
            role=UserRole.ADMIN,
            theme=UserTheme.LIGHT,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"Default admin user created with ID: {admin_user.id}")
        return admin_user
        
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")
        db.rollback()
        raise


def create_system_configs(db: Session) -> None:
    """
    创建系统默认配置
    
    Args:
        db: 数据库会话
    """
    try:
        # 默认系统配置
        default_configs = [
            {
                "config_key": "system.name",
                "config_value": "IP地址管理系统",
                "description": "系统名称"
            },
            {
                "config_key": "system.version",
                "config_value": "1.0.0",
                "description": "系统版本"
            },
            {
                "config_key": "system.timezone",
                "config_value": "Asia/Shanghai",
                "description": "系统时区"
            },
            {
                "config_key": "pagination.default_page_size",
                "config_value": "50",
                "description": "默认分页大小"
            },
            {
                "config_key": "pagination.max_page_size",
                "config_value": "1000",
                "description": "最大分页大小"
            },
            {
                "config_key": "security.password_min_length",
                "config_value": "8",
                "description": "密码最小长度"
            },
            {
                "config_key": "security.session_timeout",
                "config_value": "30",
                "description": "会话超时时间（分钟）"
            },
            {
                "config_key": "alert.default_utilization_threshold",
                "config_value": "80.0",
                "description": "默认IP使用率警报阈值（百分比）"
            },
            {
                "config_key": "alert.notification_enabled",
                "config_value": "true",
                "description": "是否启用警报通知"
            },
            {
                "config_key": "backup.auto_backup_enabled",
                "config_value": "false",
                "description": "是否启用自动备份"
            },
            {
                "config_key": "backup.retention_days",
                "config_value": "30",
                "description": "备份保留天数"
            },
            {
                "config_key": "audit.log_retention_days",
                "config_value": "90",
                "description": "审计日志保留天数"
            }
        ]
        
        created_count = 0
        for config_data in default_configs:
            # 检查配置是否已存在
            existing_config = db.query(SystemConfig).filter(
                SystemConfig.config_key == config_data["config_key"]
            ).first()
            
            if not existing_config:
                config = SystemConfig(**config_data)
                db.add(config)
                created_count += 1
        
        if created_count > 0:
            db.commit()
            logger.info(f"Created {created_count} system configurations")
        else:
            logger.info("All system configurations already exist")
            
    except Exception as e:
        logger.error(f"Failed to create system configurations: {e}")
        db.rollback()
        raise


def create_default_tags(db: Session) -> None:
    """
    创建默认标签
    
    Args:
        db: 数据库会话
    """
    try:
        # 默认标签
        default_tags = [
            {
                "name": "服务器",
                "color": "#007bff",
                "description": "服务器设备"
            },
            {
                "name": "网络设备",
                "color": "#28a745",
                "description": "路由器、交换机等网络设备"
            },
            {
                "name": "打印机",
                "color": "#ffc107",
                "description": "打印机设备"
            },
            {
                "name": "办公设备",
                "color": "#17a2b8",
                "description": "办公室其他设备"
            },
            {
                "name": "测试环境",
                "color": "#fd7e14",
                "description": "测试环境使用的IP"
            },
            {
                "name": "生产环境",
                "color": "#dc3545",
                "description": "生产环境使用的IP"
            },
            {
                "name": "开发环境",
                "color": "#6f42c1",
                "description": "开发环境使用的IP"
            },
            {
                "name": "重要",
                "color": "#e83e8c",
                "description": "重要的IP地址"
            }
        ]
        
        created_count = 0
        for tag_data in default_tags:
            # 检查标签是否已存在
            existing_tag = db.query(Tag).filter(Tag.name == tag_data["name"]).first()
            
            if not existing_tag:
                tag = Tag(**tag_data)
                db.add(tag)
                created_count += 1
        
        if created_count > 0:
            db.commit()
            logger.info(f"Created {created_count} default tags")
        else:
            logger.info("All default tags already exist")
            
    except Exception as e:
        logger.error(f"Failed to create default tags: {e}")
        db.rollback()
        raise


def seed_database() -> bool:
    """
    执行数据库种子数据初始化
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        logger.info("Starting database seeding...")
        
        with get_db_session() as db:
            # 创建默认admin用户
            admin_user = create_default_admin_user(db)
            
            # 创建系统配置
            create_system_configs(db)
            
            # 创建默认标签
            create_default_tags(db)
            
            logger.info("Database seeding completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        return False


def reset_admin_password(new_password: str = "admin123") -> bool:
    """
    重置admin用户密码
    
    Args:
        new_password: 新密码
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        with get_db_session() as db:
            admin_user = db.query(User).filter(User.username == "admin").first()
            
            if not admin_user:
                logger.error("Admin user not found")
                return False
            
            admin_user.password_hash = hash_password(new_password)
            db.commit()
            
            logger.info("Admin password reset successfully")
            return True
            
    except Exception as e:
        logger.error(f"Failed to reset admin password: {e}")
        return False


def create_demo_data(db: Session) -> None:
    """
    创建演示数据（可选）
    仅在开发环境使用
    
    Args:
        db: 数据库会话
    """
    try:
        from app.models.subnet import Subnet
        from app.models.ip_address import IPAddress, IPStatus
        
        # 检查是否已有演示数据
        existing_subnet = db.query(Subnet).filter(Subnet.network == "192.168.1.0/24").first()
        if existing_subnet:
            logger.info("Demo data already exists")
            return
        
        # 获取admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.warning("Admin user not found, skipping demo data creation")
            return
        
        # 创建演示网段
        demo_subnet = Subnet(
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            description="演示网段 - 办公网络",
            vlan_id=100,
            location="总部办公室",
            created_by=admin_user.id
        )
        
        db.add(demo_subnet)
        db.flush()  # 获取subnet ID
        
        # 创建一些演示IP地址
        demo_ips = [
            {
                "ip_address": "192.168.1.1",
                "status": IPStatus.RESERVED,
                "hostname": "gateway",
                "device_type": "路由器",
                "description": "网关设备"
            },
            {
                "ip_address": "192.168.1.10",
                "status": IPStatus.ALLOCATED,
                "hostname": "server-01",
                "device_type": "服务器",
                "assigned_to": "IT部门",
                "description": "主服务器"
            },
            {
                "ip_address": "192.168.1.20",
                "status": IPStatus.ALLOCATED,
                "hostname": "printer-01",
                "device_type": "打印机",
                "assigned_to": "行政部门",
                "description": "办公打印机"
            }
        ]
        
        for ip_data in demo_ips:
            ip_address = IPAddress(
                subnet_id=demo_subnet.id,
                allocated_by=admin_user.id if ip_data["status"] != IPStatus.AVAILABLE else None,
                allocated_at=datetime.utcnow() if ip_data["status"] != IPStatus.AVAILABLE else None,
                **ip_data
            )
            db.add(ip_address)
        
        db.commit()
        logger.info("Demo data created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create demo data: {e}")
        db.rollback()
        raise


def seed_with_demo_data() -> bool:
    """
    执行包含演示数据的数据库种子初始化
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        logger.info("Starting database seeding with demo data...")
        
        with get_db_session() as db:
            # 执行基本种子数据
            create_default_admin_user(db)
            create_system_configs(db)
            create_default_tags(db)
            
            # 创建演示数据
            create_demo_data(db)
            
            logger.info("Database seeding with demo data completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Database seeding with demo data failed: {e}")
        return False


if __name__ == "__main__":
    # 直接运行此脚本时执行种子数据初始化
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--with-demo":
        success = seed_with_demo_data()
    else:
        success = seed_database()
    
    if success:
        print("数据库种子数据初始化成功")
    else:
        print("数据库种子数据初始化失败")
        sys.exit(1)