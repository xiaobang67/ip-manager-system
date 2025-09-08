#!/usr/bin/env python3
"""
修复admin用户密码
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt

# 数据库连接配置
DATABASE_URL = "mysql+pymysql://ipam_user:ipam_pass123@mysql:3306/ipam"

def fix_admin_password():
    """修复admin用户密码"""
    try:
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print('数据库连接成功')
        
        # 查询admin用户
        result = session.execute(text('SELECT id, username, password_hash FROM users WHERE username = :username'), 
                               {'username': 'admin'})
        user = result.fetchone()
        
        if user:
            print(f'找到用户: {user.username} (ID: {user.id})')
            print(f'当前密码哈希: {user.password_hash[:50]}...')
            
            # 测试当前密码
            test_passwords = ['admin', 'admin123', 'password', '123456']
            current_password = None
            
            for password in test_passwords:
                try:
                    if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                        print(f'✅ 当前密码是: {password}')
                        current_password = password
                        break
                except Exception as e:
                    print(f'验证密码 "{password}" 时出错: {e}')
            
            if not current_password:
                print('❌ 无法验证当前密码，将重置为 "admin"')
            
            # 生成新的admin密码哈希
            new_password = 'admin'
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # 更新数据库中的密码
            session.execute(text('UPDATE users SET password_hash = :hash WHERE username = :username'), 
                          {'hash': new_hash.decode('utf-8'), 'username': 'admin'})
            session.commit()
            
            print(f'✅ admin用户密码已重置为: {new_password}')
            print(f'新密码哈希: {new_hash.decode("utf-8")[:50]}...')
            
            # 验证新密码
            result = session.execute(text('SELECT password_hash FROM users WHERE username = :username'), 
                                   {'username': 'admin'})
            updated_user = result.fetchone()
            
            if bcrypt.checkpw(new_password.encode('utf-8'), updated_user.password_hash.encode('utf-8')):
                print('✅ 新密码验证成功')
            else:
                print('❌ 新密码验证失败')
                
        else:
            print('❌ 未找到admin用户')
        
        session.close()
        
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_admin_password()