#!/usr/bin/env python3
"""
企业IP地址管理系统 - 后端启动脚本
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 加载环境变量
load_dotenv(os.path.join(current_dir, 'config.env'))

def main():
    """主函数"""
    # 检查是否安装了必要的依赖
    try:
        import fastapi
        import sqlalchemy
        import MySQLdb
        print("✓ 依赖检查通过")
    except ImportError as e:
        print(f"✗ 缺少必要依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 获取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    print(f"🚀 启动企业IP地址管理系统后端服务")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print(f"🔄 调试模式: {'开启' if debug else '关闭'}")
    print("-" * 50)
    
    # 启动服务器
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=debug,
            access_log=True,
            log_level="info" if debug else "warning",
            env_file="config.env",
            forwarded_allow_ips="*",
            proxy_headers=True,
            http="h11",
            ws="none"  # 禁用websocket
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()