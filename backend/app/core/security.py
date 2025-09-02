"""
安全相关工具模块
包含密码加密、JWT token生成和验证等功能
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from .config import settings
import secrets
import string

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
    
    Returns:
        bool: 密码匹配返回True，否则返回False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希值
    
    Args:
        password: 明文密码
    
    Returns:
        str: 哈希密码
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码到token中的数据
        expires_delta: 过期时间增量，如果为None则使用默认值
    
    Returns:
        str: JWT访问令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建刷新令牌
    
    Args:
        data: 要编码到token中的数据
        expires_delta: 过期时间增量，如果为None则使用默认值
    
    Returns:
        str: JWT刷新令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
        token_type: 令牌类型 ("access" 或 "refresh")
    
    Returns:
        dict: 解码后的令牌数据，验证失败返回None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # 检查令牌类型
        if payload.get("type") != token_type:
            return None
            
        # 检查过期时间
        exp = payload.get("exp")
        if exp is None or datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
            
        return payload
    except JWTError:
        return None


def generate_random_password(length: int = 12) -> str:
    """
    生成随机密码
    
    Args:
        length: 密码长度
    
    Returns:
        str: 随机密码
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password: 要验证的密码
    
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if len(password) < 8:
        return False, "密码长度至少8位"
    
    if not any(c.isupper() for c in password):
        return False, "密码必须包含至少一个大写字母"
    
    if not any(c.islower() for c in password):
        return False, "密码必须包含至少一个小写字母"
    
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含至少一个数字"
    
    return True, ""


async def get_current_user_from_token(token: str):
    """
    从token获取当前用户
    
    Args:
        token: JWT访问令牌
    
    Returns:
        User: 用户对象，验证失败返回None
    """
    try:
        payload = verify_token(token, "access")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # 导入放在函数内部避免循环导入
        from app.core.database import get_db
        from app.models.user import User
        
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user
        finally:
            db.close()
    except Exception:
        return None


class TokenData:
    """Token数据类"""
    def __init__(self, user_id: int, username: str, role: str):
        self.user_id = user_id
        self.username = username
        self.role = role