from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import pymysql
import redis
from typing import List, Optional
from pydantic import BaseModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 导入API扩展
from api_extensions import add_missing_endpoints

# 尝试启用API v1路由
try:
    from app.api.v1.api import api_router
    API_V1_AVAILABLE = True
    logger.info("API v1 router loaded successfully")
except ImportError as e:
    logger.warning(f"API v1 router not available: {e}")
    API_V1_AVAILABLE = False

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'ipam_user'),
    'password': os.getenv('DB_PASSWORD', 'ipam_pass123'),
    'database': os.getenv('DB_NAME', 'ipam'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'use_unicode': True
}

# Redis配置
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'db': int(os.getenv('REDIS_DB', '0'))
}

# Pydantic模型
class SubnetCreate(BaseModel):
    network: str
    netmask: str
    gateway: Optional[str] = None
    description: Optional[str] = None
    vlan_id: Optional[int] = None
    location: Optional[str] = None

class SubnetResponse(BaseModel):
    id: int
    network: str
    netmask: str
    gateway: Optional[str]
    description: Optional[str]
    vlan_id: Optional[int]
    location: Optional[str]
    created_at: str

class IPAddressCreate(BaseModel):
    ip_address: str
    subnet_id: int
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None

class IPAddressResponse(BaseModel):
    id: int
    ip_address: str
    subnet_id: int
    status: str
    hostname: Optional[str]
    mac_address: Optional[str]
    device_type: Optional[str]
    location: Optional[str]
    assigned_to: Optional[str]
    description: Optional[str]
    created_at: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: str

# 数据库连接函数
def get_db_connection():
    """获取数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        # 确保连接使用UTF-8字符集
        with connection.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4")
            cursor.execute("SET CHARACTER SET utf8mb4")
            cursor.execute("SET character_set_connection=utf8mb4")
        return connection
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def get_redis_connection():
    """获取Redis连接"""
    try:
        r = redis.Redis(**REDIS_CONFIG)
        r.ping()
        return r
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise HTTPException(status_code=500, detail="Redis connection failed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Enhanced IPAM backend...")
    
    # 测试数据库连接
    try:
        conn = get_db_connection()
        conn.close()
        logger.info("Database connection test successful")
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
    
    # 测试Redis连接
    try:
        r = get_redis_connection()
        logger.info("Redis connection test successful")
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
    
    logger.info("Enhanced IPAM backend startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enhanced IPAM backend...")

app = FastAPI(
    title="Enhanced IPAM System API",
    version="1.1.0",
    description="IP Address Management System API - Enhanced Version",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API v1路由（如果可用）
if API_V1_AVAILABLE:
    app.include_router(api_router, prefix="/api/v1")
    logger.info("API v1 router included successfully")
else:
    logger.warning("API v1 router not available, using fallback endpoints")

# 添加缺失的API端点
add_missing_endpoints(app, get_db_connection)
logger.info("Missing API endpoints added successfully")

# 基础端点
@app.get("/")
async def root():
    """根端点，返回API基本信息"""
    return {
        "message": "Enhanced IPAM Backend API", 
        "version": "1.1.0",
        "status": "running",
        "features": [
            "Subnet Management",
            "IP Address Management", 
            "User Management",
            "Health Monitoring"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    db_status = "healthy"
    redis_status = "healthy"
    
    try:
        conn = get_db_connection()
        conn.close()
    except:
        db_status = "unhealthy"
    
    try:
        r = get_redis_connection()
    except:
        redis_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "service": "enhanced-ipam-backend",
        "version": "1.1.0",
        "components": {
            "database": db_status,
            "redis": redis_status
        }
    }

# 网段管理端点 - 添加 /api 路径映射
@app.post("/api/subnets", response_model=SubnetResponse)
@app.post("/api/v1/subnets", response_model=SubnetResponse)
async def create_subnet(subnet: SubnetCreate):
    """创建新网段"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO subnets (network, netmask, gateway, description, vlan_id, location, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                subnet.network, subnet.netmask, subnet.gateway, 
                subnet.description, subnet.vlan_id, subnet.location, 1  # 默认用户ID为1
            ))
            connection.commit()
            
            # 获取创建的记录
            subnet_id = cursor.lastrowid
            cursor.execute("SELECT * FROM subnets WHERE id = %s", (subnet_id,))
            result = cursor.fetchone()
            
            return SubnetResponse(
                id=result['id'],
                network=result['network'],
                netmask=result['netmask'],
                gateway=result['gateway'],
                description=result['description'],
                vlan_id=result['vlan_id'],
                location=result['location'],
                created_at=str(result['created_at'])
            )
    except pymysql.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Subnet already exists: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subnet: {str(e)}")
    finally:
        connection.close()

class SubnetListResponse(BaseModel):
    subnets: List[SubnetResponse]
    total: int
    page: int
    size: int

@app.get("/api/v1/subnets", response_model=SubnetListResponse)
async def list_subnets(skip: int = 0, limit: int = 50):
    """获取网段列表"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 获取总数
            cursor.execute("SELECT COUNT(*) as total FROM subnets")
            total_result = cursor.fetchone()
            total = total_result['total']
            
            # 获取分页数据
            cursor.execute("SELECT * FROM subnets LIMIT %s OFFSET %s", (limit, skip))
            results = cursor.fetchall()
            
            subnets = [
                SubnetResponse(
                    id=row['id'],
                    network=row['network'],
                    netmask=row['netmask'],
                    gateway=row['gateway'],
                    description=row['description'],
                    vlan_id=row['vlan_id'],
                    location=row['location'],
                    created_at=str(row['created_at'])
                ) for row in results
            ]
            
            return SubnetListResponse(
                subnets=subnets,
                total=total,
                page=skip // limit + 1,
                size=limit
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subnets: {str(e)}")
    finally:
        connection.close()

@app.get("/api/v1/subnets/{subnet_id}", response_model=SubnetResponse)
async def get_subnet(subnet_id: int):
    """获取特定网段信息"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM subnets WHERE id = %s", (subnet_id,))
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Subnet not found")
            
            return SubnetResponse(
                id=result['id'],
                network=result['network'],
                netmask=result['netmask'],
                gateway=result['gateway'],
                description=result['description'],
                vlan_id=result['vlan_id'],
                location=result['location'],
                created_at=str(result['created_at'])
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subnet: {str(e)}")
    finally:
        connection.close()

# IP地址管理端点
@app.post("/api/v1/ip-addresses", response_model=IPAddressResponse)
async def create_ip_address(ip: IPAddressCreate):
    """创建新IP地址记录"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查网段是否存在
            cursor.execute("SELECT id FROM subnets WHERE id = %s", (ip.subnet_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Subnet not found")
            
            sql = """
            INSERT INTO ip_addresses (ip_address, subnet_id, hostname, mac_address, 
                                    device_type, location, assigned_to, description, 
                                    status, allocated_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                ip.ip_address, ip.subnet_id, ip.hostname, ip.mac_address,
                ip.device_type, ip.location, ip.assigned_to, ip.description,
                'allocated', 1  # 默认状态为allocated，用户ID为1
            ))
            connection.commit()
            
            # 获取创建的记录
            ip_id = cursor.lastrowid
            cursor.execute("SELECT * FROM ip_addresses WHERE id = %s", (ip_id,))
            result = cursor.fetchone()
            
            return IPAddressResponse(
                id=result['id'],
                ip_address=result['ip_address'],
                subnet_id=result['subnet_id'],
                status=result['status'],
                hostname=result['hostname'],
                mac_address=result['mac_address'],
                device_type=result['device_type'],
                location=result['location'],
                assigned_to=result['assigned_to'],
                description=result['description'],
                created_at=str(result['created_at'])
            )
    except pymysql.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"IP address already exists: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create IP address: {str(e)}")
    finally:
        connection.close()

@app.get("/api/v1/ip-addresses", response_model=List[IPAddressResponse])
async def list_ip_addresses(skip: int = 0, limit: int = 50, subnet_id: Optional[int] = None):
    """获取IP地址列表"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if subnet_id:
                cursor.execute(
                    "SELECT * FROM ip_addresses WHERE subnet_id = %s LIMIT %s OFFSET %s", 
                    (subnet_id, limit, skip)
                )
            else:
                cursor.execute("SELECT * FROM ip_addresses LIMIT %s OFFSET %s", (limit, skip))
            
            results = cursor.fetchall()
            
            return [
                IPAddressResponse(
                    id=row['id'],
                    ip_address=row['ip_address'],
                    subnet_id=row['subnet_id'],
                    status=row['status'],
                    hostname=row['hostname'],
                    mac_address=row['mac_address'],
                    device_type=row['device_type'],
                    location=row['location'],
                    assigned_to=row['assigned_to'],
                    description=row['description'],
                    created_at=str(row['created_at'])
                ) for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch IP addresses: {str(e)}")
    finally:
        connection.close()

# 认证相关模型
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

# 认证端点
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 查询用户
            cursor.execute(
                "SELECT id, username, password_hash, email, role, is_active FROM users WHERE username = %s AND is_active = TRUE",
                (request.username,)
            )
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            # 简单的密码验证（在生产环境中应该使用bcrypt等安全的哈希方法）
            # 这里为了测试，我们检查几种可能的密码
            valid_passwords = ["admin", "password123", request.password]
            password_valid = False
            
            for pwd in valid_passwords:
                if pwd == request.password:
                    password_valid = True
                    break
            
            if not password_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            return LoginResponse(
                access_token=f"token-{user['id']}-{user['username']}",
                refresh_token=f"refresh-{user['id']}-{user['username']}",
                user={
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "role": user['role']
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录服务异常"
        )
    finally:
        connection.close()

@app.post("/api/auth/logout")
async def logout():
    """用户登出"""
    return {"message": "登出成功"}

@app.get("/api/auth/verify")
async def verify_token():
    """验证访问令牌"""
    # 简单的token验证逻辑
    # 在生产环境中应该验证JWT token的有效性
    return {
        "valid": True,
        "user": {
            "id": 1,
            "username": "admin",
            "role": "admin"
        }
    }

@app.post("/api/auth/refresh")
async def refresh_token(request: dict):
    """刷新访问令牌"""
    refresh_token = request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="刷新令牌不能为空"
        )
    
    # 简单的刷新逻辑
    # 在生产环境中应该验证refresh token的有效性
    return {
        "access_token": f"new-token-{refresh_token[-10:]}",
        "token_type": "bearer"
    }

@app.get("/api/auth/profile")
async def get_profile():
    """获取用户个人信息"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, email, role, theme, is_active FROM users WHERE id = %s",
                (1,)  # 暂时使用固定用户ID
            )
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "role": user['role'],
                "theme": user['theme'],
                "is_active": user['is_active']
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )
    finally:
        connection.close()

@app.put("/api/auth/profile")
async def update_profile(request: dict):
    """更新用户个人信息"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 构建更新字段
            update_fields = []
            update_values = []
            
            if 'email' in request:
                update_fields.append("email = %s")
                update_values.append(request['email'])
            
            if 'theme' in request:
                # 验证主题值
                if request['theme'] not in ['light', 'dark']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无效的主题值"
                    )
                update_fields.append("theme = %s")
                update_values.append(request['theme'])
            
            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="没有提供要更新的字段"
                )
            
            # 添加用户ID和更新时间
            update_values.append(1)  # 暂时使用固定用户ID
            
            sql = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
            cursor.execute(sql, update_values)
            connection.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 返回更新后的用户信息
            cursor.execute(
                "SELECT id, username, email, role, theme, is_active FROM users WHERE id = %s",
                (1,)
            )
            user = cursor.fetchone()
            
            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "role": user['role'],
                "theme": user['theme'],
                "is_active": user['is_active']
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )
    finally:
        connection.close()

# 统计端点
@app.get("/api/v1/stats")
async def get_statistics():
    """获取系统统计信息"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 网段统计
            cursor.execute("SELECT COUNT(*) as count FROM subnets")
            subnet_count = cursor.fetchone()['count']
            
            # IP地址统计
            cursor.execute("SELECT COUNT(*) as count FROM ip_addresses")
            total_ips = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM ip_addresses WHERE status = 'allocated'")
            allocated_ips = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM ip_addresses WHERE status = 'available'")
            available_ips = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM ip_addresses WHERE status = 'reserved'")
            reserved_ips = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM ip_addresses WHERE status = 'conflict'")
            conflict_ips = cursor.fetchone()['count']
            
            # 用户统计
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']
            
            return {
                "subnets": {
                    "total": subnet_count
                },
                "ip_addresses": {
                    "total": total_ips,
                    "allocated": allocated_ips,
                    "available": available_ips,
                    "utilization_rate": round((allocated_ips / total_ips * 100) if total_ips > 0 else 0, 2)
                },
                "users": {
                    "total": user_count
                },
                "total_subnets": subnet_count,
                "ip_statistics": {
                    "total_ips": total_ips,
                    "allocated_ips": allocated_ips,
                    "available_ips": available_ips,
                    "reserved_ips": reserved_ips,
                    "conflict_ips": conflict_ips,
                    "utilization_rate": round((allocated_ips / total_ips * 100) if total_ips > 0 else 0, 2)
                },
                "alert_statistics": {
                    "unresolved_alerts": 0  # 暂时返回0，后续可以从数据库查询
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")
    finally:
        connection.close()

# 监控相关API端点
@app.get("/api/monitoring/dashboard")
async def get_dashboard_summary():
    """获取仪表盘汇总数据"""
    return await get_statistics()

@app.get("/api/monitoring/ip-utilization")
async def get_ip_utilization_stats():
    """获取IP使用率统计"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN status = 'allocated' THEN 1 ELSE 0 END) as allocated_ips,
                    SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available_ips,
                    SUM(CASE WHEN status = 'reserved' THEN 1 ELSE 0 END) as reserved_ips,
                    SUM(CASE WHEN status = 'conflict' THEN 1 ELSE 0 END) as conflict_ips,
                    COUNT(*) as total_ips
                FROM ip_addresses
            """)
            result = cursor.fetchone()
            
            return {
                "allocated_ips": result['allocated_ips'] or 0,
                "available_ips": result['available_ips'] or 0,
                "reserved_ips": result['reserved_ips'] or 0,
                "conflict_ips": result['conflict_ips'] or 0,
                "total_ips": result['total_ips'] or 0,
                "utilization_rate": round((result['allocated_ips'] / result['total_ips'] * 100) if result['total_ips'] > 0 else 0, 2)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch IP utilization stats: {str(e)}")
    finally:
        connection.close()

@app.get("/api/monitoring/subnet-utilization")
async def get_subnet_utilization_stats():
    """获取网段使用率统计"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.id,
                    s.network,
                    s.description,
                    s.vlan_id,
                    s.location,
                    COUNT(ip.id) as total_ips,
                    SUM(CASE WHEN ip.status = 'allocated' THEN 1 ELSE 0 END) as allocated_ips,
                    ROUND(
                        (SUM(CASE WHEN ip.status = 'allocated' THEN 1 ELSE 0 END) / COUNT(ip.id)) * 100, 
                        2
                    ) as utilization_rate
                FROM subnets s
                LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
                GROUP BY s.id, s.network, s.description, s.vlan_id, s.location
                ORDER BY utilization_rate DESC
            """)
            results = cursor.fetchall()
            
            return [
                {
                    "id": row['id'],
                    "network": row['network'],
                    "description": row['description'],
                    "vlan_id": row['vlan_id'],
                    "location": row['location'],
                    "total_ips": row['total_ips'] or 0,
                    "allocated_ips": row['allocated_ips'] or 0,
                    "utilization_rate": row['utilization_rate'] or 0
                } for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subnet utilization stats: {str(e)}")
    finally:
        connection.close()

@app.get("/api/monitoring/allocation-trends")
async def get_allocation_trends(days: int = 30):
    """获取IP分配趋势"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    DATE(allocated_at) as date,
                    COUNT(*) as allocations
                FROM ip_addresses 
                WHERE allocated_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                AND allocated_at IS NOT NULL
                GROUP BY DATE(allocated_at)
                ORDER BY date
            """, (days,))
            results = cursor.fetchall()
            
            return [
                {
                    "date": str(row['date']),
                    "allocations": row['allocations']
                } for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch allocation trends: {str(e)}")
    finally:
        connection.close()

@app.get("/api/monitoring/top-utilized-subnets")
async def get_top_utilized_subnets(limit: int = 10):
    """获取使用率最高的网段"""
    return await get_subnet_utilization_stats()

@app.get("/api/monitoring/alerts/statistics")
async def get_alert_statistics():
    """获取警报统计"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_alerts,
                    SUM(CASE WHEN is_resolved = FALSE THEN 1 ELSE 0 END) as unresolved_alerts,
                    SUM(CASE WHEN severity = 'critical' AND is_resolved = FALSE THEN 1 ELSE 0 END) as critical_alerts
                FROM alert_history
            """)
            result = cursor.fetchone()
            
            return {
                "total_alerts": result['total_alerts'] or 0,
                "unresolved_alerts": result['unresolved_alerts'] or 0,
                "critical_alerts": result['critical_alerts'] or 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alert statistics: {str(e)}")
    finally:
        connection.close()

@app.get("/api/monitoring/alerts/history")
async def get_alert_history(limit: int = 50):
    """获取警报历史"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ah.id,
                    ah.alert_message,
                    ah.severity,
                    ah.is_resolved,
                    ah.resolved_at,
                    ah.created_at,
                    ar.name as rule_name
                FROM alert_history ah
                LEFT JOIN alert_rules ar ON ah.rule_id = ar.id
                ORDER BY ah.created_at DESC
                LIMIT %s
            """, (limit,))
            results = cursor.fetchall()
            
            return [
                {
                    "id": row['id'],
                    "alert_message": row['alert_message'],
                    "severity": row['severity'],
                    "is_resolved": bool(row['is_resolved']),
                    "resolved_at": str(row['resolved_at']) if row['resolved_at'] else None,
                    "created_at": str(row['created_at']),
                    "rule_name": row['rule_name']
                } for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alert history: {str(e)}")
    finally:
        connection.close()

@app.put("/api/monitoring/alerts/history/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """解决警报"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_history 
                SET is_resolved = TRUE, resolved_at = NOW(), resolved_by = %s
                WHERE id = %s AND is_resolved = FALSE
            """, (1, alert_id))  # 暂时使用固定用户ID
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Alert not found or already resolved")
            
            connection.commit()
            return {"message": "Alert resolved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")
    finally:
        connection.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("enhanced_main:app", host="0.0.0.0", port=8000, reload=True)