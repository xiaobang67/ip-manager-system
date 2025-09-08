#!/usr/bin/env python3
"""
测试密码验证修复
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import verify_password, get_password_hash

def test_password_verification():
    """测试密码验证功能"""
    print("=== 密码验证功能测试 ===")
    
    # 测试密码
    test_password = 'admin'
    wrong_password = 'wrong_password'
    
    # 生成哈希
    hashed = get_password_hash(test_password)
    
    print(f"原始密码: {test_password}")
    print(f"哈希密码: {hashed}")
    print(f"正确密码验证: {verify_password(test_password, hashed)}")
    print(f"错误密码验证: {verify_password(wrong_password, hashed)}")
    
    # 验证结果
    if verify_password(test_password, hashed) and not verify_password(wrong_password, hashed):
        print("✅ 密码验证功能正常")
        return True
    else:
        print("❌ 密码验证功能异常")
        return False

if __name__ == "__main__":
    test_password_verification()