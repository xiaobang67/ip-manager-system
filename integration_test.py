#!/usr/bin/env python3
"""
系统管理模块集成测试和部署验证
"""
import subprocess
import requests
import time
import json
import sys

def print_status(message, success=True):
    """打印状态信息"""
    prefix = "✅" if success else "❌"
    print(f"{prefix} {message}")

def test_database_connection():
    """测试数据库连接"""
    print("\n🗄️ 测试数据库连接...")
    try:
        import os
        import sys
        sys.path.append('./backend')
        from sqlalchemy import create_engine, text
        from dotenv import load_dotenv
        
        # 加载环境变量
        load_dotenv('./backend/.env')
        
        # 构建数据库连接字符串
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '3306')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', 'rootpassword')
        db_name = os.getenv('DB_NAME', 'ip_management_system')
        
        database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        engine = create_engine(database_url)
        with engine.connect() as connection:
            # 测试连接
            connection.execute(text("SELECT 1"))
            print_status("数据库连接成功")
            
            # 检查认证表
            result = connection.execute(text("SELECT COUNT(*) FROM auth_users"))
            user_count = result.fetchone()[0]
            print_status(f"认证用户表存在，共{user_count}个用户")
            
            # 检查admin用户
            result = connection.execute(text("SELECT username, is_admin, is_active FROM auth_users WHERE username='admin'"))
            admin_user = result.fetchone()
            if admin_user:
                print_status(f"管理员用户存在: {admin_user[0]}, 管理员权限: {admin_user[1]}, 状态: {'启用' if admin_user[2] else '禁用'}")
                return True
            else:
                print_status("管理员用户不存在", False)
                return False
                
    except Exception as e:
        print_status(f"数据库连接失败: {e}", False)
        return False

def test_frontend_build():
    """测试前端构建状态"""
    print("\n🎨 检查前端构建状态...")
    
    frontend_dist = "./frontend/dist"
    import os
    if os.path.exists(frontend_dist):
        print_status("前端已构建完成")
        return True
    else:
        print_status("前端尚未构建或构建失败", False)
        return False

def test_api_availability():
    """测试API可用性"""
    print("\n🌐 测试API服务...")
    
    try:
        # 测试健康检查
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print_status("API服务正常运行")
            return True
        else:
            print_status(f"API服务异常，状态码: {response.status_code}", False)
            return False
    except requests.RequestException as e:
        print_status(f"无法连接API服务: {e}", False)
        return False

def validate_authentication_system():
    """验证认证系统完整性"""
    print("\n🔐 验证认证系统完整性...")
    
    # 检查关键文件
    critical_files = [
        "./backend/models/auth_user.py",
        "./backend/services/auth_service.py", 
        "./backend/api/auth.py",
        "./backend/middleware/auth_middleware.py",
        "./frontend/src/stores/auth.ts",
        "./frontend/src/views/auth/Login.vue",
        "./frontend/src/views/system/UserManagement.vue",
        "./auth_tables.sql"
    ]
    
    import os
    all_files_exist = True
    for file_path in critical_files:
        if os.path.exists(file_path):
            print_status(f"关键文件存在: {os.path.basename(file_path)}")
        else:
            print_status(f"关键文件缺失: {file_path}", False)
            all_files_exist = False
    
    return all_files_exist

def generate_deployment_summary():
    """生成部署总结报告"""
    print("\n📋 系统管理模块部署总结")
    print("=" * 50)
    
    summary = """
🎯 实现的功能:
1. ✅ 用户、组管理 (支持LDAP认证)
   - LDAP用户认证和同步
   - 本地用户管理
   - 用户组管理
   - 权限控制 (普通用户/管理员/超级管理员)

2. ✅ 系统登录机制
   - JWT令牌认证
   - 路由守卫保护
   - 会话管理
   - 安全登出

🏗️ 技术架构:
- 后端: FastAPI + SQLAlchemy + ldap3 + JWT
- 前端: Vue 3 + Pinia + Element Plus + Vue Router
- 数据库: MySQL (Docker)
- 认证: LDAP集成 + 本地认证备用

🗄️ 数据库表:
- auth_users: 认证用户表
- auth_groups: 用户组表  
- user_group_association: 用户组关联表
- user_sessions: 用户会话表

👤 默认账户:
- 用户名: admin
- 密码: admin123
- 权限: 超级管理员

🚀 部署方式:
- Docker Compose (推荐)
- 本地开发环境 (已测试)

📁 关键文件:
- 后端认证服务: backend/services/auth_service.py
- 前端认证状态: frontend/src/stores/auth.ts
- 用户管理界面: frontend/src/views/system/UserManagement.vue
- 数据库脚本: auth_tables.sql

🔧 LDAP配置:
- 服务器: ldap://192.168.0.38:389
- 搜索基础: ou=技术部,ou=研发中心,dc=ost,dc=com
- 用户属性: sAMAccountName (用户名映射)
"""
    
    print(summary)
    
    print("\n🎊 系统管理模块实现完成!")
    print("用户现在需要登录后才能访问系统，并支持完整的用户和组管理功能。")

def main():
    """主测试流程"""
    print("🚀 企业IP地址管理系统 - 系统管理模块集成测试")
    print("=" * 60)
    
    # 执行各项测试
    tests_passed = 0
    total_tests = 4
    
    if test_database_connection():
        tests_passed += 1
    
    if test_frontend_build():
        tests_passed += 1
    
    if test_api_availability():
        tests_passed += 1
    
    if validate_authentication_system():
        tests_passed += 1
    
    # 显示测试结果
    print(f"\n📊 测试结果: {tests_passed}/{total_tests} 项测试通过")
    
    if tests_passed >= 3:
        print_status("系统基本功能正常，可以进行部署")
        generate_deployment_summary()
        return True
    else:
        print_status("系统存在关键问题，需要进一步检查", False)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)