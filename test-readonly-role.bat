@echo off
echo ========================================
echo 只读角色功能测试脚本
echo ========================================

cd /d "%~dp0"

echo 测试只读角色功能...
echo.

echo 1. 检查只读用户是否存在...
python -c "
import sys
import os
sys.path.append('backend')
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import get_settings
from app.models.user import User, UserRole

try:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    readonly_user = db.query(User).filter(User.role == UserRole.READONLY).first()
    if readonly_user:
        print(f'✅ 找到只读用户: {readonly_user.username}')
        print(f'   角色: {readonly_user.role}')
        print(f'   状态: {'激活' if readonly_user.is_active else '未激活'}')
    else:
        print('❌ 未找到只读用户')
        
    db.close()
except Exception as e:
    print(f'❌ 检查失败: {e}')
"

echo.
echo 2. 检查数据库角色枚举是否更新...
python -c "
import sys
import os
sys.path.append('backend')
from sqlalchemy import create_engine, text
from app.core.config import get_settings

try:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text(\"SHOW COLUMNS FROM users LIKE 'role'\"))
        column_info = result.fetchone()
        if column_info and 'readonly' in str(column_info):
            print('✅ 数据库角色枚举已更新，包含readonly选项')
        else:
            print('❌ 数据库角色枚举未包含readonly选项')
            print(f'   当前枚举: {column_info}')
except Exception as e:
    print(f'❌ 检查失败: {e}')
"

echo.
echo ========================================
echo 测试完成
echo ========================================
echo.
echo 如果测试通过，可以使用以下凭据登录测试只读功能：
echo   用户名: readonly
echo   密码: readonly123
echo.
echo 预期行为：
echo   - 只能看到搜索框，无操作按钮
echo   - 无法访问用户管理等其他页面
echo   - 可以正常查询和查看IP地址信息
echo.
pause