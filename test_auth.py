#!/usr/bin/env python3
"""
测试认证模块导入
"""
import sys
import os

# 添加后端目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    print("正在测试认证模块导入...")
    
    # 测试基础模块导入
    from api.auth import router
    print(f"✅ 认证路由导入成功")
    print(f"✅ 路由数量: {len(router.routes)}")
    
    # 列出所有路由
    print("\n📋 可用的认证路由:")
    for route in router.routes:
        methods = list(route.methods) if hasattr(route, 'methods') else ['GET']
        print(f"  - {route.path} {methods}")
    
    # 测试应用主模块
    print("\n正在测试主应用模块...")
    from app.main import app
    print(f"✅ 主应用导入成功")
    
    # 检查路由注册
    print(f"✅ 应用总路由数: {len(app.routes)}")
    
    print("\n📋 所有应用路由:")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = list(route.methods) if hasattr(route, 'methods') else ['GET']
            print(f"  - {route.path} {methods}")
    
    print("\n🎉 所有测试通过！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
