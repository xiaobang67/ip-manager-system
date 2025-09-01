#!/usr/bin/env python3
"""
生成密码哈希
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    """生成密码哈希"""
    return pwd_context.hash(password)

if __name__ == "__main__":
    password = "admin123"
    hashed = hash_password(password)
    print(f"密码: {password}")
    print(f"哈希值: {hashed}")