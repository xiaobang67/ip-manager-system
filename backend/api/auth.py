"""
认证API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database.connection import get_db
from services.auth_service import auth_service
from app.auth_schemas import (
    LoginRequest, LoginResponse, RefreshTokenRequest, LogoutRequest,
    AuthUserResponse, AuthUserCreate, AuthUserUpdate, CurrentUserResponse,
    AuthGroupResponse, AuthGroupCreate, AuthGroupUpdate,
    PasswordChangeRequest, AuthStatsResponse
)
from app.schemas import MessageResponse
from models.auth_user import AuthUser, AuthGroup, UserSession

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AuthUser:
    """获取当前用户"""
    token = credentials.credentials
    user = auth_service.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 确保返回的是用户对象而不是SQLAlchemy模型实例
    return user

def get_current_admin_user(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """获取当前管理员用户"""
    if not bool(current_user.is_admin_value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

def get_current_superuser(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """获取当前超级用户"""
    if not bool(current_user.is_superuser_value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级用户权限"
        )
    return current_user


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        # 认证用户
        user = auth_service.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
            
        if not bool(user.is_active):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户账户已被禁用"
            )
        
        # 创建令牌
        access_token = auth_service.create_access_token({"sub": user.username})
        refresh_token = auth_service.create_refresh_token({"sub": user.username})
        
        # 创建会话
        client_ip = request.client.host if request.client else ""
        user_agent = request.headers.get("user-agent", "")
        auth_service.create_user_session(
            db, user, access_token, refresh_token, client_ip, user_agent
        )
        
        # 创建用户响应对象
        user_response = AuthUserResponse(
            id=int(user.id),
            username=str(user.username),
            real_name=str(user.real_name) if user.real_name else "",
            display_name=str(user.display_name) if user.display_name else "",
            email=str(user.email) if user.email else "",
            employee_id=str(user.employee_id) if user.employee_id else "",
            is_admin=bool(user.is_admin),
            is_superuser=bool(user.is_superuser),
            is_ldap_user=bool(user.is_ldap_user),
            login_count=int(user.login_count),
            created_at=user.created_at,
            updated_at=user.updated_at,
            department=None,  # 设置为None而不是空字符串
            groups=[str(group.name) for group in user.groups],
            permissions=[]
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=auth_service.jwt_config["access_token_expire_minutes"] * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    logout_data: LogoutRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户登出"""
    try:
        if logout_data.refresh_token:
            # 使刷新令牌失效
            session = db.query(UserSession).filter_by(
                refresh_token=logout_data.refresh_token,
                user_id=int(current_user.id)
            ).first()
            if session:
                session.is_active = False
                db.commit()
        
        return MessageResponse(message="登出成功")
        
    except Exception as e:
        logger.error(f"登出错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        payload = auth_service.verify_token(refresh_data.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        username = payload.get("sub")
        user = db.query(AuthUser).filter_by(username=username, is_active=True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 验证会话
        session = db.query(UserSession).filter_by(
            refresh_token=refresh_data.refresh_token,
            user_id=int(user.id_value),
            is_active=True
        ).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="会话已失效"
            )
        
        # 创建新的访问令牌
        access_token = auth_service.create_access_token({"sub": user.username_value})
        new_refresh_token = auth_service.create_refresh_token({"sub": user.username_value})
        
        # 更新会话
        session.session_token = access_token
        session.refresh_token = new_refresh_token
        db.commit()
        
        # 创建用户响应对象
        user_response = AuthUserResponse(
            id=int(getattr(user, "id_value", getattr(user, "id", 0)) or 0),
            username=str(getattr(user, "username_value", getattr(user, "username", "")) or ""),
            real_name=str(getattr(user, "real_name_value", getattr(user, "real_name", "")) or ""),
            display_name=str(getattr(user, "display_name_value", getattr(user, "display_name", "")) or ""),
            email=str(getattr(user, "email_value", getattr(user, "email", "")) or ""),
            employee_id=str(getattr(user, "employee_id_value", getattr(user, "employee_id", "")) or ""),
            is_admin=bool(getattr(user, "is_admin_value", getattr(user, "is_admin", False)) or False),
            is_superuser=bool(getattr(user, "is_superuser_value", getattr(user, "is_superuser", False)) or False),
            is_ldap_user=bool(getattr(user, "is_ldap_user_value", getattr(user, "is_ldap_user", False)) or False),
            login_count=int(getattr(user, "login_count", 0) or 0),
            created_at=getattr(user, "created_at", None),
            updated_at=getattr(user, "updated_at", None),
            department=None,  # 设置为None而不是空字符串
            groups=[str(getattr(group, "name_value", getattr(group, "name", "")) or "") for group in user.groups],
            permissions=[]
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=auth_service.jwt_config["access_token_expire_minutes"] * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败"
        )


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(current_user: AuthUser = Depends(get_current_user)):
    """获取当前用户信息"""
    group_names = [group.name for group in current_user.groups]
    permissions = []  # 这里可以根据用户组和角色设置权限
    
    if bool(current_user.is_superuser):
        permissions.extend(["superuser", "admin", "user"])
    elif bool(current_user.is_admin):
        permissions.extend(["admin", "user"])
    else:
        permissions.append("user")
    
    return CurrentUserResponse(
        id=int(current_user.id),
        username=str(current_user.username),
        real_name=str(current_user.real_name) if current_user.real_name else "",
        display_name=str(current_user.display_name) if current_user.display_name else "",
        email=str(current_user.email) if current_user.email else "",
        employee_id=str(current_user.employee_id) if current_user.employee_id else "",
        is_admin=bool(current_user.is_admin),
        is_superuser=bool(current_user.is_superuser),
        department=None,  # 设置为None而不是空字符串
        groups=group_names,
        permissions=permissions
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        # 对于LDAP用户，不允许修改密码
        if bool(current_user.is_ldap_user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LDAP用户无法修改密码，请联系管理员"
            )
        
        # 验证原密码
        if not current_user.password_hash or not auth_service.verify_password(
            password_data.old_password, current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )
        
        # 更新密码
        current_user.password_hash = auth_service.hash_password(password_data.new_password)
        db.commit()
        
        return MessageResponse(message="密码修改成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )


# 用户管理API (管理员权限)
@router.get("/users", response_model=List[AuthUserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_ldap_user: Optional[bool] = None,
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    query = db.query(AuthUser)
    
    if search:
        query = query.filter(
            AuthUser.username.contains(search) |
            AuthUser.real_name.contains(search) |
            AuthUser.email.contains(search)
        )
    
    if is_active is not None:
        query = query.filter(AuthUser.is_active == is_active)
        
    if is_ldap_user is not None:
        query = query.filter(AuthUser.is_ldap_user == is_ldap_user)
    
    users = query.offset(skip).limit(limit).all()
    result = []
    for user in users:
        result.append(AuthUserResponse(
            id=int(user.id),
            username=str(user.username),
            real_name=str(user.real_name) if user.real_name else "",
            display_name=str(user.display_name) if user.display_name else "",
            email=str(user.email) if user.email else "",
            employee_id=str(user.employee_id) if user.employee_id else "",
            is_admin=bool(user.is_admin),
            is_superuser=bool(user.is_superuser),
            is_ldap_user=bool(user.is_ldap_user),
            login_count=int(user.login_count),
            created_at=user.created_at,
            updated_at=user.updated_at,
            department=None,
            groups=[str(group.name) for group in user.groups],
            permissions=[]
        ))
    return result


@router.post("/users", response_model=AuthUserResponse)
async def create_user(
    user_data: AuthUserCreate,
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建用户"""
    try:
        # 检查用户名是否已存在
        existing_user = db.query(AuthUser).filter_by(username=user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 创建用户
        user_dict = user_data.dict()
        password = user_dict.pop('password', None)
        
        new_user = AuthUser(**user_dict)
        
        if password and not bool(user_data.is_ldap_user):
            new_user.password_hash = auth_service.hash_password(password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 创建用户响应对象
        user_response = AuthUserResponse(
            id=int(new_user.id),
            username=str(new_user.username),
            real_name=str(new_user.real_name) if new_user.real_name else "",
            display_name=str(new_user.display_name) if new_user.display_name else "",
            email=str(new_user.email) if new_user.email else "",
            employee_id=str(new_user.employee_id) if new_user.employee_id else "",
            is_admin=bool(new_user.is_admin),
            is_superuser=bool(new_user.is_superuser),
            is_ldap_user=bool(new_user.is_ldap_user),
            login_count=int(new_user.login_count),
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
            department=None,  # 设置为None而不是直接使用new_user.department
            groups=[str(group.name) for group in new_user.groups],
            permissions=[]
        )
        
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )


@router.put("/users/{user_id}", response_model=AuthUserResponse)
async def update_user(
    user_id: int,
    user_data: AuthUserUpdate,
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户"""
    try:
        user = db.query(AuthUser).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新用户信息
        update_data = user_data.dict(exclude_unset=True)
        password = update_data.pop('password', None)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        if password and not bool(user.is_ldap_user):
            user.password_hash = auth_service.hash_password(password)
        
        db.commit()
        db.refresh(user)
        
        # 创建用户响应对象
        user_response = AuthUserResponse(
            id=int(user.id),
            username=str(user.username),
            real_name=str(user.real_name) if user.real_name else "",
            display_name=str(user.display_name) if user.display_name else "",
            email=str(user.email) if user.email else "",
            employee_id=str(user.employee_id) if user.employee_id else "",
            is_admin=bool(user.is_admin),
            is_superuser=bool(user.is_superuser),
            is_ldap_user=bool(user.is_ldap_user),
            login_count=int(user.login_count),
            created_at=user.created_at,
            updated_at=user.updated_at,
            department=None,  # 设置为None而不是空字符串
            groups=[group.name for group in user.groups],
            permissions=[]
        )
        
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户失败"
        )


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除用户"""
    try:
        user = db.query(AuthUser).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        if int(user.id_value) == int(current_user.id_value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己"
            )
        
        db.delete(user)
        db.commit()
        
        return MessageResponse(message="用户删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )


# 用户组管理API
@router.get("/groups", response_model=List[AuthGroupResponse])
async def get_groups(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_ldap_group: Optional[bool] = None,
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取用户组列表"""
    query = db.query(AuthGroup)
    
    if search:
        query = query.filter(
            AuthGroup.name.contains(search) |
            AuthGroup.display_name.contains(search)
        )
    
    if is_active is not None:
        query = query.filter(AuthGroup.is_active == is_active)
        
    if is_ldap_group is not None:
        query = query.filter(AuthGroup.is_ldap_group == is_ldap_group)
    
    groups = query.offset(skip).limit(limit).all()
    
    # 添加用户数量
    result = []
    for group in groups:
        group_data = AuthGroupResponse.from_orm(group)
        group_data.user_count = len(group.users)
        result.append(group_data)
    
    return result


@router.post("/groups", response_model=AuthGroupResponse)
async def create_group(
    group_data: AuthGroupCreate,
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建用户组"""
    try:
        # 检查组名是否已存在
        existing_group = db.query(AuthGroup).filter_by(name=group_data.name).first()
        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="组名已存在"
            )
        
        new_group = AuthGroup(**group_data.dict())
        db.add(new_group)
        db.commit()
        db.refresh(new_group)
        
        return AuthGroupResponse.from_orm(new_group)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户组错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户组失败"
        )


@router.put("/groups/{group_id}", response_model=AuthGroupResponse)
async def update_group(
    group_id: int,
    group_data: AuthGroupUpdate,
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户组"""
    try:
        group = db.query(AuthGroup).filter_by(id=group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户组不存在"
            )
        
        # 不允许修改LDAP组的某些字段
        if bool(group.is_ldap_group) and group_data.name and group_data.name != group.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改LDAP组的名称"
            )
        
        update_data = group_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)
        
        db.commit()
        db.refresh(group)
        
        # 创建组响应对象
        group_response = AuthGroupResponse(
            id=int(group.id),
            name=str(group.name),
            display_name=str(group.display_name) if group.display_name else "",
            description=str(group.description) if group.description else "",
            is_ldap_group=bool(group.is_ldap_group),
            ldap_dn=str(group.ldap_dn) if group.ldap_dn else "",
            is_active=bool(group.is_active),
            created_at=group.created_at,
            updated_at=group.updated_at,
            user_count=len(group.users)
        )
        
        return group_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户组错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户组失败"
        )


@router.delete("/groups/{group_id}", response_model=MessageResponse)
async def delete_group(
    group_id: int,
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除用户组"""
    try:
        group = db.query(AuthGroup).filter_by(id=group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户组不存在"
            )
        
        if bool(group.is_ldap_group):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除LDAP组"
            )
        
        db.delete(group)
        db.commit()
        
        return MessageResponse(message="用户组删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户组错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户组失败"
        )


# 系统管理API (超级用户权限)
@router.get("/stats", response_model=AuthStatsResponse)
async def get_auth_stats(
    current_user: AuthUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取认证统计信息"""
    try:
        total_users = db.query(AuthUser).count()
        active_users = db.query(AuthUser).filter_by(is_active=True).count()
        ldap_users = db.query(AuthUser).filter_by(is_ldap_user=True).count()
        local_users = db.query(AuthUser).filter_by(is_ldap_user=False).count()
        
        total_groups = db.query(AuthGroup).count()
        ldap_groups = db.query(AuthGroup).filter_by(is_ldap_group=True).count()
        
        active_sessions = db.query(UserSession).filter_by(is_active=True).count()
        
        return AuthStatsResponse(
            total_users=total_users,
            active_users=active_users,
            ldap_users=ldap_users,
            local_users=local_users,
            total_groups=total_groups,
            ldap_groups=ldap_groups,
            active_sessions=active_sessions
        )
        
    except Exception as e:
        logger.error(f"获取统计信息错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )