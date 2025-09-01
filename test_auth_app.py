#!/usr/bin/env python3
"""
简化的认证系统测试应用
只包含认证相关功能，避免其他依赖问题
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import os
import sys
from dotenv import load_dotenv

# 添加后端目录到Python路径
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.append(backend_dir)

# 只导入认证相关的路由
from api.auth import router as auth_router
from middleware.auth_middleware import JWTAuthMiddleware

# 加载环境变量
load_dotenv(os.path.join(backend_dir, '.env'))

# 创建FastAPI应用实例
app = FastAPI(
    title="认证系统测试应用",
    description="用于测试LDAP认证和JWT认证功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        media_type="application/json; charset=utf-8"
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
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
            "detail": str(exc)
        },
        media_type="application/json; charset=utf-8"
    )

# 根路径
@app.get("/")
async def root():
    """根路径，返回系统信息"""
    return JSONResponse(
        content={
            "message": "认证系统测试 API",
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
            "message": "认证系统运行正常"
        },
        media_type="application/json; charset=utf-8"
    )

# 注册认证路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证管理"])

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("认证系统测试应用启动中...")
    print(f"API文档地址: http://localhost:8000/docs")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    print("认证系统测试应用已关闭")

if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        "test_auth_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True
    )