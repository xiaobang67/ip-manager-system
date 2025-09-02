#!/usr/bin/env python3
"""
数据库设置测试脚本
用于验证数据库设计和初始化功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试所有模块导入"""
    print("测试模块导入...")
    
    try:
        # 测试核心模块
        from app.core.config import settings
        from app.core.database import Base, engine, SessionLocal
        from app.core.health_check import DatabaseHealthChecker
        from app.core.seed_data import seed_database
        
        # 测试模型导入
        from app.models import (
            User, Subnet, IPAddress, CustomField, CustomFieldValue,
            Tag, AuditLog, SystemConfig, AlertRule, AlertHistory
        )
        
        print("✅ 所有模块导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False


def test_model_definitions():
    """测试模型定义"""
    print("测试模型定义...")
    
    try:
        from app.models.user import User, UserRole, UserTheme
        from app.models.subnet import Subnet
        from app.models.ip_address import IPAddress, IPStatus
        
        # 测试枚举值
        assert UserRole.ADMIN == "admin"
        assert UserTheme.LIGHT == "light"
        assert IPStatus.AVAILABLE == "available"
        
        # 测试模型属性
        assert hasattr(User, 'username')
        assert hasattr(User, 'password_hash')
        assert hasattr(Subnet, 'network')
        assert hasattr(IPAddress, 'ip_address')
        
        print("✅ 模型定义验证成功")
        return True
        
    except Exception as e:
        print(f"❌ 模型定义验证失败: {e}")
        return False


def test_database_config():
    """测试数据库配置"""
    print("测试数据库配置...")
    
    try:
        from app.core.config import settings
        from app.core.database import engine
        
        # 检查配置
        assert settings.DATABASE_URL is not None
        assert "mysql" in settings.DATABASE_URL
        
        # 检查引擎配置
        assert engine is not None
        
        print("✅ 数据库配置验证成功")
        print(f"数据库URL: {settings.DATABASE_URL}")
        return True
        
    except Exception as e:
        print(f"❌ 数据库配置验证失败: {e}")
        return False


def test_health_checker():
    """测试健康检查器"""
    print("测试健康检查器...")
    
    try:
        from app.core.health_check import DatabaseHealthChecker, health_checker
        
        # 创建健康检查器实例
        checker = DatabaseHealthChecker()
        assert checker is not None
        
        # 测试方法存在
        assert hasattr(checker, 'perform_health_check')
        assert hasattr(checker, 'get_health_summary')
        
        print("✅ 健康检查器验证成功")
        return True
        
    except Exception as e:
        print(f"❌ 健康检查器验证失败: {e}")
        return False


def test_seed_data_functions():
    """测试种子数据功能"""
    print("测试种子数据功能...")
    
    try:
        from app.core.seed_data import (
            hash_password, 
            create_default_admin_user,
            create_system_configs,
            create_default_tags
        )
        
        # 测试密码加密
        hashed = hash_password("test123")
        assert hashed is not None
        assert len(hashed) > 20  # bcrypt哈希应该比较长
        
        print("✅ 种子数据功能验证成功")
        return True
        
    except Exception as e:
        print(f"❌ 种子数据功能验证失败: {e}")
        return False


def test_alembic_migration():
    """测试Alembic迁移文件"""
    print("测试Alembic迁移文件...")
    
    try:
        migration_file = Path(__file__).parent / "alembic" / "versions" / "001_initial_database_schema.py"
        
        if migration_file.exists():
            # 读取迁移文件内容
            content = migration_file.read_text(encoding='utf-8')
            
            # 检查关键内容
            assert "def upgrade()" in content
            assert "def downgrade()" in content
            assert "users" in content
            assert "subnets" in content
            assert "ip_addresses" in content
            
            print("✅ Alembic迁移文件验证成功")
            return True
        else:
            print("❌ Alembic迁移文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ Alembic迁移文件验证失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始数据库设置测试...\n")
    
    tests = [
        test_imports,
        test_model_definitions,
        test_database_config,
        test_health_checker,
        test_seed_data_functions,
        test_alembic_migration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"❌ 测试执行异常: {e}\n")
    
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！数据库设计和初始化功能正常")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关配置")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)