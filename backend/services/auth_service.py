""" 
认证服务
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from config.auth_config import JWT_CONFIG
from models.auth_user import AuthUser, AuthGroup, UserSession

logger = logging.getLogger(__name__)

class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_config = JWT_CONFIG

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[AuthUser]:
        """本地用户认证"""
        return self._authenticate_local_user(db, username, password)

    def _authenticate_local_user(self, db: Session, username: str, password: str) -> Optional[AuthUser]:
        """本地用户认证"""
        user = db.query(AuthUser).filter_by(username=username).first()
        
        if user and user.password_hash and self.verify_password(password, user.password_hash):
            user.last_login = datetime.now()
            user.login_count = user.login_count + 1
            db.commit()
            return user
            
        return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """加密密码"""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.jwt_config["access_token_expire_minutes"])
        to_encode.update({"exp": expire})
        
        return jwt.encode(
            to_encode,
            self.jwt_config["secret_key"],
            algorithm=self.jwt_config["algorithm"]
        )

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.jwt_config["refresh_token_expire_days"])
        to_encode.update({"exp": expire})
        
        return jwt.encode(
            to_encode,
            self.jwt_config["secret_key"],
            algorithm=self.jwt_config["algorithm"]
        )

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_config["secret_key"],
                algorithms=[self.jwt_config["algorithm"]]
            )
            return payload
        except JWTError:
            return None

    def create_user_session(self, db: Session, user: AuthUser, access_token: str, 
                          refresh_token: str, ip_address: str = "", 
                          user_agent: str = "") -> UserSession:
        """创建用户会话"""
        expires_at = datetime.utcnow() + timedelta(minutes=self.jwt_config["access_token_expire_minutes"])
        
        session = UserSession(
            user_id=int(user.id),
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        
        db.add(session)
        db.commit()
        return session

    def invalidate_user_session(self, db: Session, session_token: str):
        """失效用户会话"""
        session = db.query(UserSession).filter_by(session_token=session_token).first()
        if session:
            session.is_active = False
            db.commit()

    def get_user_by_token(self, db: Session, token: str) -> Optional[AuthUser]:
        """通过令牌获取用户"""
        # 处理可能带有"Bearer "前缀的令牌
        if token.startswith("Bearer "):
            token = token[7:]  # 去掉"Bearer "前缀
        
        payload = self.verify_token(token)
        if not payload:
            return None
            
        username = payload.get("sub")
        if not username:
            return None
            
        user = db.query(AuthUser).filter_by(username=username, is_active=True).first()
        return user


# 全局认证服务实例
auth_service = AuthService()