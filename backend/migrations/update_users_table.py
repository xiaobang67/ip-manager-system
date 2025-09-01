"""
数据库迁移脚本 - 更新用户表结构
添加缺失的认证相关字段
"""

from sqlalchemy import text

# 添加认证相关字段的SQL
MIGRATION_SQL = """
-- 添加认证相关字段到users表
ALTER TABLE users 
ADD COLUMN ldap_dn VARCHAR(500) COMMENT 'LDAP DN',
ADD COLUMN auth_source VARCHAR(20) DEFAULT 'ldap' COMMENT '认证来源（ldap/local）',
ADD COLUMN password_hash VARCHAR(255) COMMENT '密码哈希（本地用户）',
ADD COLUMN last_login DATETIME COMMENT '最后登录时间',
ADD COLUMN login_count INT DEFAULT 0 COMMENT '登录次数',
ADD COLUMN is_admin TINYINT DEFAULT 0 COMMENT '是否管理员';

-- 添加索引
ALTER TABLE users 
ADD INDEX idx_ldap_dn (ldap_dn),
ADD INDEX idx_auth_source (auth_source);
"""

def run_migration(db_session):
    """执行数据库迁移"""
    try:
        # 拆分SQL语句并逐个执行
        statements = MIGRATION_SQL.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement:  # 跳过空语句
                print(f"执行SQL: {statement[:100]}...")
                db_session.execute(text(statement))
        
        db_session.commit()
        print("数据库迁移完成!")
        
    except Exception as e:
        db_session.rollback()
        print(f"数据库迁移失败: {e}")
        raise

if __name__ == "__main__":
    # 如果直接运行此脚本，连接数据库并执行迁移
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from database.connection import SessionLocal
    
    db = SessionLocal()
    try:
        run_migration(db)
    finally:
        db.close()