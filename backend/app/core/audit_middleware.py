from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import json
import time
from app.services.audit_service import AuditService
from app.core.database import get_db
from app.core.security import get_current_user_from_token


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志记录中间件"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/refresh"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        # 跳过不需要审计的路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # 跳过GET请求（只记录修改操作）
        if request.method == "GET":
            return await call_next(request)
        
        # 获取请求信息
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 获取请求体（如果存在）
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body.decode())
            except:
                request_body = None
        
        # 执行请求
        response = await call_next(request)
        
        # 只记录成功的修改操作
        if 200 <= response.status_code < 300:
            try:
                # 从token获取用户信息
                user_id = await self._get_user_id_from_request(request)
                if user_id:
                    # 解析路径和操作
                    action, entity_type, entity_id = self._parse_request_info(
                        request.url.path, request.method, request_body
                    )
                    
                    if action and entity_type:
                        # 记录审计日志
                        db = next(get_db())
                        try:
                            audit_service = AuditService(db)
                            audit_service.log_operation(
                                user_id=user_id,
                                action=action,
                                entity_type=entity_type,
                                entity_id=entity_id,
                                new_values=request_body,
                                ip_address=client_ip,
                                user_agent=user_agent
                            )
                        finally:
                            db.close()
            except Exception as e:
                # 审计日志记录失败不应该影响正常请求
                print(f"Audit logging failed: {e}")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        return request.client.host if request.client else "unknown"
    
    async def _get_user_id_from_request(self, request: Request) -> Optional[int]:
        """从请求中获取用户ID"""
        try:
            authorization = request.headers.get("authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return None
            
            token = authorization.split(" ")[1]
            user = await get_current_user_from_token(token)
            return user.id if user else None
        except:
            return None
    
    def _parse_request_info(self, path: str, method: str, body: dict) -> tuple:
        """解析请求信息，提取操作类型、实体类型和实体ID"""
        action = None
        entity_type = None
        entity_id = None
        
        # 解析路径
        path_parts = path.strip("/").split("/")
        
        if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "v1":
            endpoint = path_parts[2]
            
            # 映射端点到实体类型
            entity_mapping = {
                "ips": "ip",
                "subnets": "subnet", 
                "users": "user",
                "custom-fields": "custom_field",
                "tags": "tag"
            }
            
            entity_type = entity_mapping.get(endpoint)
            
            # 解析操作类型
            if method == "POST":
                if len(path_parts) > 3:
                    # POST /api/v1/ips/allocate -> ALLOCATE
                    action_part = path_parts[3]
                    if action_part == "allocate":
                        action = "ALLOCATE"
                    elif action_part == "reserve":
                        action = "RESERVE"
                    else:
                        action = "CREATE"
                else:
                    action = "CREATE"
            elif method == "PUT" or method == "PATCH":
                if len(path_parts) > 3:
                    # PUT /api/v1/ips/123/release -> RELEASE
                    if len(path_parts) > 4:
                        action_part = path_parts[4]
                        if action_part == "release":
                            action = "RELEASE"
                        elif action_part == "reserve":
                            action = "RESERVE"
                        else:
                            action = "UPDATE"
                    else:
                        action = "UPDATE"
                        try:
                            entity_id = int(path_parts[3])
                        except:
                            pass
                else:
                    action = "UPDATE"
            elif method == "DELETE":
                action = "DELETE"
                if len(path_parts) > 3:
                    try:
                        entity_id = int(path_parts[3])
                    except:
                        pass
        
        return action, entity_type, entity_id


def create_audit_middleware(exclude_paths: Optional[list] = None):
    """创建审计中间件的工厂函数"""
    def middleware(app):
        return AuditMiddleware(app, exclude_paths)
    return middleware