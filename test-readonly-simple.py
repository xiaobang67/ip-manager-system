#!/usr/bin/env python3
"""
简化的只读角色功能测试脚本
"""
import os
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_readonly_role():
    """测试只读角色功能"""
    try:
        # 从环境变量或默认值构建数据库URL
        mysql_user = os.getenv('MYSQL_USER', 'ipam_user')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'ipam_pass123')
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = os.getenv('MYSQL_PORT', '3306')
        mysql_database = os.getenv('MYSQL_DATABASE', 'ipam')
        
        database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        logger.info(f"连接数据库: {mysql_host}:{mysql_port}/{mysql_database}")
        
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            print("========================================")
            print("只读角色功能测试")
            print("========================================")
            print()
            
            # 1. 检查只读用户是否存在
            print("1. 检查只读用户是否存在...")
            result = db.execute(text("SELECT username, role, is_active FROM users WHERE role = 'readonly'"))
            readonly_users = result.fetchall()
            
            if readonly_users:
                for user in readonly_users:
                    print(f"✅ 找到只读用户: {user.username}")
                    print(f"   角色: {user.role}")
                    print(f"   状态: {'激活' if user.is_active else '未激活'}")
            else:
                print("❌ 未找到只读用户")
                return False
            
            print()
            
            # 2. 检查数据库角色枚举是否更新
            print("2. 检查数据库角色枚举是否更新...")
            result = db.execute(text("SHOW COLUMNS FROM users LIKE 'role'"))
            column_info = result.fetchone()
            
            if column_info and 'readonly' in str(column_info):
                print("✅ 数据库角色枚举已更新，包含readonly选项")
                print(f"   枚举值: {column_info}")
            else:
                print("❌ 数据库角色枚举未包含readonly选项")
                print(f"   当前枚举: {column_info}")
                return False
            
            print()
            print("========================================")
            print("测试完成 - 所有检查通过！")
            print("========================================")
            print()
            print("可以使用以下凭据登录测试只读功能：")
            print("  用户名: readonly")
            print("  密码: readonly123")
            print()
            print("预期行为：")
            print("  - 只能看到搜索框，无操作按钮")
            print("  - 无法访问用户管理等其他页面")
            print("  - 可以正常查询和查看IP地址信息")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 测试脚本执行失败: {e}")
        return False

if __name__ == "__main__":
    test_readonly_role()