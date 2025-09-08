#!/usr/bin/env python3
"""
一键修复所有密码哈希格式并测试统一认证服务
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import subprocess

def run_script(script_name, description):
    """运行Python脚本"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"脚本: {script_name}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        print("标准输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} 执行成功")
        else:
            print(f"❌ {description} 执行失败，返回码: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 执行 {description} 时发生异常: {e}")
        return False

def main():
    """主函数"""
    print("=== 一键修复所有密码哈希格式并测试统一认证服务 ===")
    print("此脚本将按顺序执行以下操作:")
    print("1. 修复用户密码哈希格式（SHA256 -> bcrypt）")
    print("2. 重置用户密码为已知值")
    print("3. 测试统一认证服务功能")
    
    input("\n按回车键继续...")
    
    scripts = [
        ("fix_user_passwords.py", "修复用户密码哈希格式"),
        ("reset_user_passwords.py", "重置用户密码"),
        ("test_unified_auth.py", "测试统一认证服务")
    ]
    
    success_count = 0
    total_count = len(scripts)
    
    for script_name, description in scripts:
        if run_script(script_name, description):
            success_count += 1
        else:
            print(f"\n⚠️  {description} 执行失败，是否继续？")
            choice = input("输入 'y' 继续，其他键退出: ").lower()
            if choice != 'y':
                break
    
    print(f"\n{'='*60}")
    print("执行总结")
    print('='*60)
    print(f"总脚本数: {total_count}")
    print(f"成功执行: {success_count}")
    print(f"失败数量: {total_count - success_count}")
    
    if success_count == total_count:
        print("✅ 所有操作都执行成功！")
        print("\n统一认证服务已配置完成，所有密码都使用bcrypt哈希格式。")
        print("\n主要功能:")
        print("- 用户认证: authenticate_user(username, password)")
        print("- 密码修改: change_user_password(user_id, old_password, new_password)")
        print("- 密码重置: reset_user_password(username, new_password)")
        print("- 创建用户: create_new_user(username, password, email, role)")
        print("- 密码验证: auth_service.verify_user_password(username, password)")
        print("- 获取用户: auth_service.get_user_by_username(username)")
    else:
        print("❌ 部分操作执行失败，请检查错误信息。")

if __name__ == "__main__":
    main()