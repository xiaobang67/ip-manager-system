#!/usr/bin/env python3
"""
测试admin用户密码
"""
import pymysql
import bcrypt

def test_admin_password():
    """测试admin用户密码"""
    try:
        connection = pymysql.connect(
            host='mysql',
            port=3306,
            user='ipam_user',
            password='ipam_pass123',
            database='ipam',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print('数据库连接成功')
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT username, password_hash FROM users WHERE username = %s', ('admin',))
            user = cursor.fetchone()
            
            if user:
                print(f'找到用户: {user["username"]}')
                print(f'密码哈希: {user["password_hash"]}')
                
                # 测试不同的密码
                test_passwords = ['admin', 'admin123', 'password', '123456']
                
                for password in test_passwords:
                    try:
                        # 使用bcrypt验证密码
                        is_valid = bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))
                        print(f'密码 "{password}": {"✅ 正确" if is_valid else "❌ 错误"}')
                        
                        if is_valid:
                            print(f'找到正确密码: {password}')
                            break
                    except Exception as e:
                        print(f'验证密码 "{password}" 时出错: {e}')
                
                # 生成新的admin密码哈希
                print('\n生成新的admin密码哈希:')
                new_password = 'admin'
                new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                print(f'新密码哈希: {new_hash.decode("utf-8")}')
                
                # 更新数据库中的密码
                cursor.execute('UPDATE users SET password_hash = %s WHERE username = %s', 
                             (new_hash.decode('utf-8'), 'admin'))
                connection.commit()
                print('✅ admin用户密码已更新')
                
            else:
                print('❌ 未找到admin用户')
        
        connection.close()
        
    except Exception as e:
        print(f'错误: {e}')

if __name__ == "__main__":
    test_admin_password()