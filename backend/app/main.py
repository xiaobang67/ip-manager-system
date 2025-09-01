# -*- coding: utf-8 -*-
"""
FastAPI 主应用程序
企业IP地址管理系统
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import os
from dotenv import load_dotenv
import json

# 导入路由
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.departments import router as departments_router
from api.users import router as users_router
from api.network_segments import router as network_segments_router
from api.ip_addresses import router as ip_addresses_router
from api.reserved_addresses import router as reserved_addresses_router
from api.dashboard import router as dashboard_router
from api.auth import router as auth_router
from api.system import router as system_router  # 添加系统管理路由
from middleware.auth_middleware import JWTAuthMiddleware

# 加载环境变量
load_dotenv()

# 创建FastAPI应用实例
app = FastAPI(
    title="企业IP地址管理系统",
    description="用于管理企业内部IP地址、网段、用户和部门的系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    # 确保API响应支持UTF-8编码
    openapi_url="/openapi.json"
)

# 配置CORS
origins = [
    "http://localhost:3000",  # Vue开发服务器
    "http://localhost:8080",  # Vue开发服务器备用端口
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://localhost",       # 生产环境
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # 确保支持UTF-8字符编码
    expose_headers=["*"]
)

# 添加JWT认证中间件
app.add_middleware(JWTAuthMiddleware)


# 异常处理器
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "code": exc.status_code,
            "success": False
        },
        # 确保中文字符正确显示
        media_type="application/json; charset=utf-8"
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    # 将错误信息转换为可序列化的格式
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "message": "请求参数验证失败",
            "code": 422,
            "success": False,
            "errors": error_details
        },
        media_type="application/json; charset=utf-8"
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "message": "服务器内部错误",
            "code": 500,
            "success": False,
            "detail": str(exc) if os.getenv("DEBUG_MODE", "False").lower() == "true" else None
        },
        media_type="application/json; charset=utf-8"
    )


# 根路径
@app.get("/")
async def root():
    """根路径，返回系统信息"""
    return JSONResponse(
        content={
            "message": "企业IP地址管理系统 API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        media_type="application/json; charset=utf-8"
    )


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "系统运行正常"
        },
        media_type="application/json; charset=utf-8"
    )


# 注册路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证管理"])
app.include_router(departments_router, prefix="/api/v1/departments", tags=["部门管理"])
app.include_router(users_router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(network_segments_router, prefix="/api/v1/network-segments", tags=["网段管理"])
app.include_router(ip_addresses_router, prefix="/api/v1/ip-addresses", tags=["IP地址管理"])
app.include_router(reserved_addresses_router, prefix="/api/v1/reserved-addresses", tags=["地址保留管理"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["仪表盘"])
app.include_router(system_router, prefix="/api/v1/system", tags=["系统管理"])  # 添加系统管理路由


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("企业IP地址管理系统启动中...")
    print(f"API文档地址: http://localhost:{os.getenv('API_PORT', 8000)}/docs")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    print("企业IP地址管理系统已关闭")


if __name__ == "__main__":
    # 获取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        access_log=True
    )