#!/usr/bin/env python3
"""
生成密码哈希的脚本
"""
from passlib.hash import bcrypt

def generate_password_hash(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hash(password)

if __name__ == "__main__":
    password = input("请输入要哈希的密码: ")
    hashed = generate_password_hash(password)
    print(f"密码哈希: {hashed}")