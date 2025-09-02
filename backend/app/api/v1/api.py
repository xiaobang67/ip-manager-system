from fastapi import APIRouter
from .endpoints import auth, users, subnets, ips, custom_fields, tags, monitoring, audit_logs, security
from . import performance

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["user-management"])
api_router.include_router(subnets.router, prefix="/subnets", tags=["subnet-management"])
api_router.include_router(ips.router, prefix="/ips", tags=["ip-management"])
api_router.include_router(custom_fields.router, prefix="/custom-fields", tags=["custom-fields"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(security.router, prefix="/security", tags=["security"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])

# Health check endpoint
@api_router.get("/health")
async def api_health():
    return {"status": "healthy", "api_version": "v1"}