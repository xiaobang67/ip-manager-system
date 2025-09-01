from passlib.context import CryptContext

# 创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据库中的密码哈希
db_hash = "$2b$12$jF.bbZqkQhF1mUyAXP86qOrM/G.ELhcPD3vQmcemE1hCcbS.4w1AS"

# 测试密码（应该是admin123）
test_password = "admin123"

# 验证密码
is_valid = pwd_context.verify(test_password, db_hash)
print(f"密码验证结果: {is_valid}")

# 如果验证失败，尝试其他常见密码
if not is_valid:
    common_passwords = ["admin", "password", "123456", "admin123"]
    for pwd in common_passwords:
        if pwd_context.verify(pwd, db_hash):
            print(f"找到正确密码: {pwd}")
            break
    else:
        print("未找到匹配的密码")