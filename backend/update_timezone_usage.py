#!/usr/bin/env python3
"""
更新代码中的时区使用 - 将datetime.utcnow()替换为北京时间
"""

import os
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_file_timezone_usage(file_path):
    """更新单个文件中的时区使用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 添加时区配置导入（如果还没有）
        if 'from app.core.timezone_config import' not in content:
            # 查找其他导入语句的位置
            import_pattern = r'(from datetime import.*?\n)'
            if re.search(import_pattern, content):
                content = re.sub(
                    import_pattern,
                    r'\1from app.core.timezone_config import now_beijing\n',
                    content,
                    count=1
                )
            else:
                # 如果没有datetime导入，在文件开头添加
                lines = content.split('\n')
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith('from ') or line.startswith('import '):
                        insert_pos = i + 1
                    elif line.strip() == '' and insert_pos > 0:
                        break
                
                if insert_pos > 0:
                    lines.insert(insert_pos, 'from app.core.timezone_config import now_beijing')
                    content = '\n'.join(lines)
        
        # 替换datetime.utcnow()为now_beijing()
        content = re.sub(r'datetime\.utcnow\(\)', 'now_beijing()', content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已更新文件: {file_path}")
            return True
        else:
            logger.info(f"文件无需更新: {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"更新文件 {file_path} 失败: {e}")
        return False

def find_python_files_with_utcnow():
    """查找包含datetime.utcnow()的Python文件"""
    files_to_update = []
    
    # 遍历app目录下的所有Python文件
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'datetime.utcnow()' in content:
                            files_to_update.append(file_path)
                except Exception as e:
                    logger.warning(f"无法读取文件 {file_path}: {e}")
    
    return files_to_update

def main():
    """主函数"""
    logger.info("开始更新代码中的时区使用...")
    
    # 查找需要更新的文件
    files_to_update = find_python_files_with_utcnow()
    
    if not files_to_update:
        logger.info("没有找到需要更新的文件")
        return
    
    logger.info(f"找到 {len(files_to_update)} 个需要更新的文件:")
    for file_path in files_to_update:
        logger.info(f"  - {file_path}")
    
    # 更新文件
    updated_count = 0
    for file_path in files_to_update:
        if update_file_timezone_usage(file_path):
            updated_count += 1
    
    logger.info(f"成功更新了 {updated_count} 个文件")

if __name__ == "__main__":
    main()