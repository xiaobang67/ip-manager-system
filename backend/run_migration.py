#!/usr/bin/env python3
"""
运行数据库迁移脚本
"""
import os
import sys
from alembic.config import Config
from alembic import command

def run_migration():
    """运行数据库迁移"""
    try:
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 设置alembic配置文件路径
        alembic_cfg_path = os.path.join(current_dir, 'alembic.ini')
        
        # 检查配置文件是否存在
        if not os.path.exists(alembic_cfg_path):

            return False
        
        # 创建alembic配置对象
        alembic_cfg = Config(alembic_cfg_path)
        
        # 设置脚本位置
        alembic_cfg.set_main_option('script_location', os.path.join(current_dir, 'alembic'))
        

        
        # 运行迁移到最新版本
        command.upgrade(alembic_cfg, "head")
        

        return True
        
    except Exception as e:

        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)