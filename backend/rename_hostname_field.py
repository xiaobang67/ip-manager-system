#!/usr/bin/env python3
"""
重命名数据库字段：hostname -> user_name
"""
import os
import sys
sys.path.append('.')

from app.core.database import engine
from sqlalchemy import text

def rename_hostname_field():
    """重命名hostname字段为user_name"""
    try:
        with engine.connect() as conn:
            # 检查字段是否存在
            result = conn.execute(text("SHOW COLUMNS FROM ip_addresses LIKE 'hostname'"))
            if result.fetchone():
                # 重命名字段
                conn.execute(text("ALTER TABLE ip_addresses CHANGE hostname user_name VARCHAR(255)"))
                conn.commit()
                print("✅ 字段重命名成功：hostname -> user_name")
            else:
                print("ℹ️  hostname字段不存在，可能已经重命名")
                
            # 验证新字段是否存在
            result = conn.execute(text("SHOW COLUMNS FROM ip_addresses LIKE 'user_name'"))
            if result.fetchone():
                print("✅ user_name字段已存在")
            else:
                print("❌ user_name字段不存在")
                
    except Exception as e:
        print(f"❌ 重命名失败：{e}")

if __name__ == "__main__":
    rename_hostname_field()