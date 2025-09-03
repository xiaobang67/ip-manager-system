#!/usr/bin/env python3
"""
自定义字段修复脚本
用于诊断和修复自定义字段相关的问题
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.models.custom_field import CustomField, CustomFieldValue
    from app.core.database import Base, engine, SessionLocal
    
    print("✓ 成功导入所有依赖")
except ImportError as e:
    print(f"✗ 导入依赖失败: {e}")
    print("请确保已安装所有依赖包并激活虚拟环境")
    sys.exit(1)

def check_database_connection():
    """检查数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ 数据库连接正常")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

def check_tables_exist():
    """检查自定义字段相关表是否存在"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['custom_fields', 'custom_field_values']
        missing_tables = []
        
        for table in required_tables:
            if table in tables:
                print(f"✓ 表 {table} 存在")
            else:
                print(f"✗ 表 {table} 不存在")
                missing_tables.append(table)
        
        return len(missing_tables) == 0, missing_tables
    except Exception as e:
        print(f"✗ 检查表结构失败: {e}")
        return False, []

def check_table_structure():
    """检查表结构"""
    try:
        inspector = inspect(engine)
        
        # 检查custom_fields表结构
        if 'custom_fields' in inspector.get_table_names():
            columns = inspector.get_columns('custom_fields')
            column_names = [col['name'] for col in columns]
            
            required_columns = ['id', 'entity_type', 'field_name', 'field_type', 'is_required']
            missing_columns = []
            
            print("\ncustom_fields表结构:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            for col in required_columns:
                if col not in column_names:
                    missing_columns.append(col)
            
            if missing_columns:
                print(f"✗ custom_fields表缺少列: {missing_columns}")
                return False
            else:
                print("✓ custom_fields表结构正确")
        
        # 检查custom_field_values表结构
        if 'custom_field_values' in inspector.get_table_names():
            columns = inspector.get_columns('custom_field_values')
            column_names = [col['name'] for col in columns]
            
            required_columns = ['id', 'field_id', 'entity_id', 'entity_type', 'field_value']
            missing_columns = []
            
            print("\ncustom_field_values表结构:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            for col in required_columns:
                if col not in column_names:
                    missing_columns.append(col)
            
            if missing_columns:
                print(f"✗ custom_field_values表缺少列: {missing_columns}")
                return False
            else:
                print("✓ custom_field_values表结构正确")
        
        return True
    except Exception as e:
        print(f"✗ 检查表结构失败: {e}")
        return False

def check_data_integrity():
    """检查数据完整性"""
    try:
        db = SessionLocal()
        
        # 检查自定义字段数据
        fields = db.query(CustomField).all()
        print(f"\n自定义字段数量: {len(fields)}")
        
        for field in fields:
            print(f"  字段ID: {field.id}")
            print(f"  字段名称: {field.field_name}")
            print(f"  字段类型: {field.field_type}")
            print(f"  实体类型: {field.entity_type}")
            print(f"  是否必填: {field.is_required}")
            print("  ---")
        
        # 检查字段值数据
        values = db.query(CustomFieldValue).all()
        print(f"自定义字段值数量: {len(values)}")
        
        for value in values[:5]:  # 只显示前5个
            print(f"  值ID: {value.id}")
            print(f"  字段ID: {value.field_id}")
            print(f"  实体ID: {value.entity_id}")
            print(f"  实体类型: {value.entity_type}")
            print(f"  字段值: {value.field_value}")
            print("  ---")
        
        if len(values) > 5:
            print(f"  ... 还有 {len(values) - 5} 个字段值")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ 检查数据完整性失败: {e}")
        traceback.print_exc()
        return False

def create_sample_data():
    """创建示例数据"""
    try:
        db = SessionLocal()
        
        # 检查是否已有数据
        existing_fields = db.query(CustomField).count()
        if existing_fields > 0:
            print(f"已存在 {existing_fields} 个自定义字段，跳过创建示例数据")
            db.close()
            return True
        
        # 创建示例字段
        sample_fields = [
            {
                'entity_type': 'ip',
                'field_name': '部门',
                'field_type': 'text',
                'is_required': False
            },
            {
                'entity_type': 'ip',
                'field_name': '联系人',
                'field_type': 'text',
                'is_required': False
            },
            {
                'entity_type': 'ip',
                'field_name': '优先级',
                'field_type': 'select',
                'field_options': {'options': ['高', '中', '低']},
                'is_required': False
            },
            {
                'entity_type': 'subnet',
                'field_name': '位置',
                'field_type': 'text',
                'is_required': False
            }
        ]
        
        for field_data in sample_fields:
            field = CustomField(**field_data)
            db.add(field)
        
        db.commit()
        print(f"✓ 成功创建 {len(sample_fields)} 个示例自定义字段")
        db.close()
        return True
    except Exception as e:
        print(f"✗ 创建示例数据失败: {e}")
        traceback.print_exc()
        return False

def test_api_endpoints():
    """测试API端点"""
    try:
        from app.services.custom_field_service import CustomFieldService
        from app.models.custom_field import EntityType
        
        db = SessionLocal()
        service = CustomFieldService(db)
        
        # 测试获取所有字段
        all_fields = service.get_all_fields()
        print(f"✓ 获取所有字段成功，共 {len(all_fields)} 个")
        
        # 测试按实体类型获取字段
        ip_fields = service.get_fields_by_entity_type(EntityType.IP)
        print(f"✓ 获取IP字段成功，共 {len(ip_fields)} 个")
        
        subnet_fields = service.get_fields_by_entity_type(EntityType.SUBNET)
        print(f"✓ 获取网段字段成功，共 {len(subnet_fields)} 个")
        
        # 测试获取实体字段和值
        entity_fields = service.get_entity_fields_with_values(1, EntityType.IP)
        print(f"✓ 获取实体字段成功，共 {len(entity_fields.fields)} 个")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ 测试API端点失败: {e}")
        traceback.print_exc()
        return False

def run_migration():
    """运行数据库迁移"""
    try:
        print("正在运行数据库迁移...")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✓ 数据库迁移完成")
        return True
    except Exception as e:
        print(f"✗ 数据库迁移失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=== 自定义字段修复脚本 ===\n")
    
    # 1. 检查数据库连接
    print("1. 检查数据库连接...")
    if not check_database_connection():
        print("请检查数据库配置和连接")
        return False
    
    # 2. 检查表是否存在
    print("\n2. 检查表结构...")
    tables_exist, missing_tables = check_tables_exist()
    
    if not tables_exist:
        print(f"缺少表: {missing_tables}")
        print("尝试运行数据库迁移...")
        if not run_migration():
            return False
        
        # 重新检查
        tables_exist, missing_tables = check_tables_exist()
        if not tables_exist:
            print("迁移后仍然缺少表，请检查迁移脚本")
            return False
    
    # 3. 检查表结构
    print("\n3. 检查表结构...")
    if not check_table_structure():
        print("表结构有问题，请检查迁移脚本")
        return False
    
    # 4. 检查数据完整性
    print("\n4. 检查数据完整性...")
    if not check_data_integrity():
        return False
    
    # 5. 创建示例数据（如果需要）
    print("\n5. 检查示例数据...")
    if not create_sample_data():
        return False
    
    # 6. 测试API端点
    print("\n6. 测试API端点...")
    if not test_api_endpoints():
        return False
    
    print("\n=== 修复完成 ===")
    print("✓ 所有检查都通过了！")
    print("自定义字段功能应该可以正常使用了。")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n脚本执行失败: {e}")
        traceback.print_exc()
        sys.exit(1)