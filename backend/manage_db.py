#!/usr/bin/env python3
"""
数据库管理CLI工具
提供数据库初始化、迁移、种子数据等管理功能
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import (
    wait_for_database, 
    check_database_connection,
    get_database_info,
    create_tables,
    drop_tables
)
from app.core.health_check import (
    perform_detailed_health_check,
    get_connection_pool_info
)
from app.core.seed_data import (
    seed_database,
    seed_with_demo_data,
    reset_admin_password
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_connection():
    """检查数据库连接"""
    print("检查数据库连接...")
    
    if check_database_connection():
        print("✅ 数据库连接正常")
        
        # 显示数据库信息
        db_info = get_database_info()
        print(f"数据库状态: {db_info.get('status')}")
        print(f"连接池大小: {db_info.get('pool_size')}")
        print(f"已签出连接: {db_info.get('checked_out')}")
        print(f"数据库URL: {db_info.get('url')}")
        return True
    else:
        print("❌ 数据库连接失败")
        return False


def wait_db():
    """等待数据库连接可用"""
    print("等待数据库连接...")
    
    if wait_for_database(max_retries=30, retry_interval=2):
        print("✅ 数据库连接已建立")
        return True
    else:
        print("❌ 数据库连接超时")
        return False


def health_check():
    """执行健康检查"""
    print("执行数据库健康检查...")
    
    result = perform_detailed_health_check()
    
    status_emoji = {
        "healthy": "✅",
        "degraded": "⚠️",
        "unhealthy": "❌"
    }
    
    print(f"{status_emoji.get(result.status, '❓')} 健康状态: {result.status}")
    print(f"响应时间: {result.response_time_ms:.2f}ms")
    
    if result.error:
        print(f"错误信息: {result.error}")
    
    # 显示连接池信息
    pool_info = result.details.get("connection_pool", {})
    if pool_info:
        print(f"连接池使用率: {pool_info.get('utilization_percent', 0):.1f}%")
        print(f"活跃连接: {pool_info.get('checked_out', 0)}")
        print(f"空闲连接: {pool_info.get('checked_in', 0)}")
    
    # 显示性能指标
    performance = result.details.get("performance", {})
    if performance:
        simple_query = performance.get("simple_query_ms")
        if simple_query is not None:
            print(f"简单查询响应时间: {simple_query:.2f}ms")
    
    return result.status == "healthy"


def pool_info():
    """显示连接池详细信息"""
    print("获取连接池信息...")
    
    info = get_connection_pool_info()
    
    if "error" in info:
        print(f"❌ 获取连接池信息失败: {info['error']}")
        return False
    
    # 显示配置信息
    config = info.get("pool_configuration", {})
    print("连接池配置:")
    print(f"  基础连接数: {config.get('pool_size', 'N/A')}")
    print(f"  最大溢出连接: {config.get('max_overflow', 'N/A')}")
    print(f"  连接超时: {config.get('pool_timeout', 'N/A')}秒")
    print(f"  连接回收时间: {config.get('pool_recycle', 'N/A')}秒")
    
    # 显示当前统计
    stats = info.get("current_stats", {})
    print("\n当前状态:")
    print(f"  总连接数: {stats.get('total_connections', 'N/A')}")
    print(f"  使用率: {stats.get('utilization_percent', 'N/A')}%")
    print(f"  活跃连接: {stats.get('checked_out', 'N/A')}")
    print(f"  空闲连接: {stats.get('checked_in', 'N/A')}")
    print(f"  溢出连接: {stats.get('overflow', 'N/A')}")
    print(f"  无效连接: {stats.get('invalid', 'N/A')}")
    
    # 显示建议
    recommendations = info.get("recommendations", [])
    if recommendations:
        print("\n优化建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    return True


def init_db():
    """初始化数据库表结构"""
    print("初始化数据库表结构...")
    
    try:
        create_tables()
        print("✅ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")
        return False


def drop_db():
    """删除所有数据库表"""
    print("⚠️  警告: 这将删除所有数据库表和数据!")
    
    confirm = input("请输入 'YES' 确认删除: ")
    if confirm != "YES":
        print("操作已取消")
        return False
    
    try:
        drop_tables()
        print("✅ 数据库表删除成功")
        return True
    except Exception as e:
        print(f"❌ 数据库表删除失败: {e}")
        return False


def seed():
    """执行种子数据初始化"""
    print("执行种子数据初始化...")
    
    if seed_database():
        print("✅ 种子数据初始化成功")
        print("默认管理员账号:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("  ⚠️  请在生产环境中修改默认密码!")
        return True
    else:
        print("❌ 种子数据初始化失败")
        return False


def seed_demo():
    """执行包含演示数据的种子初始化"""
    print("执行种子数据初始化（包含演示数据）...")
    
    if seed_with_demo_data():
        print("✅ 种子数据和演示数据初始化成功")
        print("默认管理员账号:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("演示数据包含:")
        print("  - 演示网段: 192.168.1.0/24")
        print("  - 示例IP地址分配")
        print("  - 默认标签和配置")
        print("  ⚠️  请在生产环境中修改默认密码!")
        return True
    else:
        print("❌ 种子数据初始化失败")
        return False


def reset_password():
    """重置admin密码"""
    print("重置admin用户密码...")
    
    new_password = input("请输入新密码 (留空使用默认密码 'admin123'): ").strip()
    if not new_password:
        new_password = "admin123"
    
    if reset_admin_password(new_password):
        print("✅ admin密码重置成功")
        return True
    else:
        print("❌ admin密码重置失败")
        return False


def migrate():
    """执行数据库迁移"""
    print("执行数据库迁移...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 数据库迁移成功")
            print(result.stdout)
            return True
        else:
            print("❌ 数据库迁移失败")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("❌ 未找到alembic命令，请确保已安装alembic")
        return False
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False


def setup():
    """完整的数据库设置流程"""
    print("开始完整的数据库设置流程...")
    
    # 1. 等待数据库连接
    if not wait_db():
        return False
    
    # 2. 执行迁移
    print("\n步骤 1: 执行数据库迁移")
    if not migrate():
        print("尝试直接创建表结构...")
        if not init_db():
            return False
    
    # 3. 初始化种子数据
    print("\n步骤 2: 初始化种子数据")
    if not seed():
        return False
    
    # 4. 执行健康检查
    print("\n步骤 3: 执行健康检查")
    if not health_check():
        print("⚠️  健康检查未通过，但设置可能仍然成功")
    
    print("\n✅ 数据库设置完成!")
    print("系统已准备就绪，可以启动应用程序")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="IPAM数据库管理工具")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 连接检查命令
    subparsers.add_parser("check", help="检查数据库连接")
    subparsers.add_parser("wait", help="等待数据库连接可用")
    subparsers.add_parser("health", help="执行健康检查")
    subparsers.add_parser("pool", help="显示连接池信息")
    
    # 数据库操作命令
    subparsers.add_parser("init", help="初始化数据库表结构")
    subparsers.add_parser("drop", help="删除所有数据库表")
    subparsers.add_parser("migrate", help="执行数据库迁移")
    
    # 数据管理命令
    subparsers.add_parser("seed", help="初始化种子数据")
    subparsers.add_parser("seed-demo", help="初始化种子数据（包含演示数据）")
    subparsers.add_parser("reset-password", help="重置admin密码")
    
    # 综合命令
    subparsers.add_parser("setup", help="完整的数据库设置流程")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应的命令
    commands = {
        "check": check_connection,
        "wait": wait_db,
        "health": health_check,
        "pool": pool_info,
        "init": init_db,
        "drop": drop_db,
        "migrate": migrate,
        "seed": seed,
        "seed-demo": seed_demo,
        "reset-password": reset_password,
        "setup": setup
    }
    
    command_func = commands.get(args.command)
    if command_func:
        try:
            success = command_func()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n操作被用户中断")
            sys.exit(1)
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            sys.exit(1)
    else:
        print(f"未知命令: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()