from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import pymysql
import redis
import ipaddress
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
    user_name: Optional[str] = None
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
    user_name: Optional[str]
    mac_address: Optional[str]
    device_type: Optional[str]
    location: Optional[str]
    assigned_to: Optional[str]
    description: Optional[str]
    allocated_at: Optional[str]
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

class DeviceTypeCreate(BaseModel):
    name: str
    code: str
    category: str
    status: str = "active"
    description: Optional[str] = None

class DeviceTypeUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None

class DeviceTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    category: str
    status: str
    description: Optional[str]
    usage_count: int
    created_at: str
    updated_at: Optional[str]

class DeviceTypeOption(BaseModel):
    code: str
    name: str
    status: str

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

def generate_ips_for_subnet_simple(connection, subnet_id: int, network: str) -> int:
    """为网段生成IP地址列表（简化版本）"""
    try:
        # 如果network不包含CIDR前缀，需要从数据库获取子网掩码
        if '/' not in network:
            with connection.cursor() as cursor:
                cursor.execute("SELECT netmask FROM subnets WHERE id = %s", (subnet_id,))
                result = cursor.fetchone()
                if result and result['netmask']:
                    netmask = result['netmask']
                    # 将点分十进制子网掩码转换为CIDR前缀长度
                    if '.' in netmask:
                        # 点分十进制格式，如 255.255.255.0
                        prefix_length = sum([bin(int(x)).count('1') for x in netmask.split('.')])
                        network = f"{network}/{prefix_length}"
                    else:
                        # 已经是前缀长度格式，如 24
                        network = f"{network}/{netmask}"
        
        net = ipaddress.ip_network(network, strict=False)
        print(f"解析网段 {network}，包含 {net.num_addresses} 个地址")
    except ValueError as e:
        print(f"网段格式错误: {network}, 错误: {e}")
        raise ValueError(f"无效的网段格式: {network}")

    # 检查网段大小，避免生成过多IP地址
    if net.num_addresses > 65536:  # /16网段
        print(f"网段过大: {network} 包含 {net.num_addresses} 个地址")
        raise ValueError("网段过大，无法自动生成所有IP地址。建议使用/17或更小的网段")

    # 批量创建IP地址数据
    ip_data_list = []
    host_count = 0
    existing_count = 0
    
    print(f"开始遍历网段 {network} 中的主机地址...")
    
    try:
        with connection.cursor() as cursor:
            for ip in net.hosts():
                host_count += 1
                ip_str = str(ip)
                
                # 检查IP是否已存在
                cursor.execute("SELECT id, subnet_id FROM ip_addresses WHERE ip_address = %s", (ip_str,))
                existing_ip = cursor.fetchone()
                
                if existing_ip and existing_ip['subnet_id'] != subnet_id:
                    # 如果IP已存在于其他网段，跳过
                    existing_count += 1
                    continue
                
                if not existing_ip:
                    ip_data_list.append((ip_str, subnet_id, 'available'))

            print(f"网段分析完成: 总主机数={host_count}, 已存在={existing_count}, 待创建={len(ip_data_list)}")

            # 批量插入IP地址
            if ip_data_list:
                print(f"开始批量创建 {len(ip_data_list)} 个IP地址...")
                
                # 使用批量插入提高性能
                sql = """
                INSERT INTO ip_addresses (ip_address, subnet_id, status, created_at)
                VALUES (%s, %s, %s, NOW())
                """
                cursor.executemany(sql, ip_data_list)
                connection.commit()
                
                print(f"成功创建 {len(ip_data_list)} 个IP地址")
                return len(ip_data_list)
            else:
                print("没有需要创建的IP地址")
                return 0
                
    except Exception as e:
        print(f"生成IP地址时发生错误: {str(e)}")
        connection.rollback()
        raise e

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

# 包含API路由（如果可用）
if API_V1_AVAILABLE:
    app.include_router(api_router, prefix="/api")
    logger.info("API router included successfully with /api prefix")
else:
    logger.warning("API router not available, using fallback endpoints")

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
            # 创建网段
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
            
            # 自动生成IP地址
            try:
                print(f"开始为网段 {subnet.network} (ID: {subnet_id}) 生成IP地址...")
                generated_count = generate_ips_for_subnet_simple(connection, subnet_id, subnet.network)
                print(f"成功生成 {generated_count} 个IP地址")
            except Exception as e:
                print(f"生成IP地址失败: {str(e)}")
                # 如果IP生成失败，不回滚网段创建，只记录错误
                logger.warning(f"网段 {subnet.network} 创建成功，但IP地址生成失败: {str(e)}")
            
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
            INSERT INTO ip_addresses (ip_address, subnet_id, user_name, mac_address, 
                                    device_type, location, assigned_to, description, 
                                    status, allocated_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                ip.ip_address, ip.subnet_id, ip.user_name, ip.mac_address,
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
                user_name=result['user_name'],
                mac_address=result['mac_address'],
                device_type=result['device_type'],
                location=result['location'],
                assigned_to=result['assigned_to'],
                description=result['description'],
                allocated_at=str(result['allocated_at']) if result['allocated_at'] else None,
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
                    user_name=row['user_name'],
                    mac_address=row['mac_address'],
                    device_type=row['device_type'],
                    location=row['location'],
                    assigned_to=row['assigned_to'],
                    description=row['description'],
                    allocated_at=str(row['allocated_at']) if row['allocated_at'] else None,
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

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# 导入统一认证服务
from auth_service import authenticate_user

# 认证端点
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    try:
        # 使用统一认证服务进行用户认证
        user = authenticate_user(request.username, request.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成JWT token
        from app.core.security import create_access_token, create_refresh_token
        
        access_token = create_access_token(
            data={"sub": str(user['id']), "username": user['username'], "role": user['role']}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user['id']), "username": user['username']}
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
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

@app.put("/api/auth/password")
async def change_password(request: ChangePasswordRequest, authorization: str = Header(None)):
    """修改用户密码"""
    # 从Authorization header中获取当前用户ID
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证令牌"
        )
    
    token = authorization.split(" ")[1]
    
    # 解析JWT token获取用户ID
    from app.core.security import verify_token
    payload = verify_token(token, "access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    user_id = int(payload.get("sub"))
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户信息"
        )
    
    try:
        # 使用统一认证服务修改密码
        from auth_service import change_user_password
        
        if change_user_password(user_id, request.old_password, request.new_password):
            return {"message": "密码修改成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码不正确或密码修改失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码过程中发生错误"
        )

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
                "total_subnets": subnet_count,
                "ip_statistics": {
                    "total_ips": total_ips,
                    "allocated_ips": allocated_ips,
                    "available_ips": available_ips,
                    "reserved_ips": reserved_ips,
                    "conflict_ips": conflict_ips,
                    "utilization_rate": round((allocated_ips / total_ips * 100) if total_ips > 0 else 0, 2)
                },
                "users": {
                    "total": user_count
                },
                "alert_statistics": {
                    "unresolved_alerts": 0
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard summary: {str(e)}")
    finally:
        connection.close()

@app.get("/api/monitoring/allocation-trends")
async def get_allocation_trends(days: int = 30):
    """获取IP分配趋势数据"""
    from datetime import datetime, timedelta
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 生成最近N天的日期范围
            sql = """
            SELECT 
                DATE(allocated_at) as date,
                COUNT(*) as allocations
            FROM ip_addresses 
            WHERE allocated_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                AND allocated_at IS NOT NULL
            GROUP BY DATE(allocated_at)
            ORDER BY date ASC
            """
            cursor.execute(sql, (days,))
            results = cursor.fetchall()
            
            # 创建完整的日期范围
            trends = []
            base_date = datetime.now() - timedelta(days=days-1)
            
            # 将数据库结果转换为字典，便于查找
            db_data = {}
            for row in results:
                date_str = row['date'].strftime("%Y-%m-%d")
                db_data[date_str] = row['allocations']
            
            # 生成完整的日期序列
            for i in range(days):
                current_date = base_date + timedelta(days=i)
                date_str = current_date.strftime("%Y-%m-%d")
                
                # 如果数据库中有该日期的数据，使用实际数据；否则使用0
                allocations = db_data.get(date_str, 0)
                
                trends.append({
                    "date": date_str,
                    "allocations": allocations
                })
            
            return trends
            
    except Exception as e:
        logger.error(f"Failed to fetch allocation trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch allocation trends: {str(e)}")
    finally:
        connection.close()

@app.get("/api/monitoring/top-utilized-subnets")
async def get_top_utilized_subnets(limit: int = 10):
    """获取使用率最高的网段"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                s.id,
                s.network,
                s.netmask,
                s.description,
                s.vlan_id,
                s.location,
                COUNT(ip.id) as total_ips,
                SUM(CASE WHEN ip.status = 'allocated' THEN 1 ELSE 0 END) as allocated_ips,
                ROUND(
                    (SUM(CASE WHEN ip.status = 'allocated' THEN 1 ELSE 0 END) * 100.0 / COUNT(ip.id)), 
                    2
                ) as utilization_rate
            FROM subnets s
            LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
            GROUP BY s.id, s.network, s.netmask, s.description, s.vlan_id, s.location
            HAVING total_ips > 0
            ORDER BY utilization_rate DESC
            LIMIT %s
            """
            cursor.execute(sql, (limit,))
            results = cursor.fetchall()
            
            subnets = []
            for row in results:
                subnets.append({
                    "id": row['id'],
                    "network": row['network'],
                    "netmask": row['netmask'],
                    "description": row['description'] or 'N/A',
                    "vlan_id": row['vlan_id'],
                    "location": row['location'] or 'N/A',
                    "total_ips": row['total_ips'],
                    "allocated_ips": row['allocated_ips'],
                    "utilization_rate": float(row['utilization_rate']) if row['utilization_rate'] else 0.0
                })
            
            return subnets
            
    except Exception as e:
        logger.error(f"Failed to fetch top utilized subnets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch top utilized subnets: {str(e)}")
    finally:
        connection.close()

# 设备类型管理端点
@app.get("/api/device-types")
async def get_device_types(skip: int = 0, limit: int = 100, search: Optional[str] = None):
    """获取设备类型列表"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 构建查询条件
            where_clause = ""
            params = []
            
            if search:
                where_clause = "WHERE name LIKE %s OR description LIKE %s"
                params.extend([f"%{search}%", f"%{search}%"])
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM device_types {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 获取设备类型使用统计
            usage_sql = """
                SELECT dt.*, 
                       COALESCE(ip_count.usage_count, 0) as usage_count
                FROM device_types dt
                LEFT JOIN (
                    SELECT device_type, COUNT(*) as usage_count
                    FROM ip_addresses 
                    WHERE device_type IS NOT NULL AND device_type != ''
                    GROUP BY device_type
                ) ip_count ON dt.code = ip_count.device_type
                {where_clause}
                ORDER BY dt.created_at DESC
                LIMIT %s OFFSET %s
            """.format(where_clause=where_clause)
            
            cursor.execute(usage_sql, params + [limit, skip])
            results = cursor.fetchall()
            
            device_types = []
            for row in results:
                device_types.append(DeviceTypeResponse(
                    id=row['id'],
                    name=row['name'],
                    code=row['code'],
                    category=row['category'],
                    status=row['status'],
                    description=row['description'],
                    usage_count=row['usage_count'],
                    created_at=str(row['created_at']),
                    updated_at=str(row['updated_at']) if row['updated_at'] else None
                ))
            
            return {
                "data": device_types,
                "total": total,
                "page": skip // limit + 1,
                "size": limit
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device types: {str(e)}")
    finally:
        connection.close()

@app.get("/api/device-types/options")
async def get_device_type_options():
    """获取设备类型选项（用于下拉选择）"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT code, name, status 
                FROM device_types 
                WHERE status = 'active'
                ORDER BY name
            """)
            results = cursor.fetchall()
            
            return [
                DeviceTypeOption(
                    code=row['code'],
                    name=row['name'],
                    status=row['status']
                ) for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device type options: {str(e)}")
    finally:
        connection.close()

@app.post("/api/device-types", response_model=DeviceTypeResponse)
async def create_device_type(device_type: DeviceTypeCreate):
    """创建设备类型"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查代码是否已存在
            cursor.execute("SELECT id FROM device_types WHERE code = %s", (device_type.code,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="设备类型代码已存在")
            
            # 创建设备类型
            sql = """
            INSERT INTO device_types (name, code, category, status, description, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(sql, (
                device_type.name,
                device_type.code,
                device_type.category,
                device_type.status,
                device_type.description
            ))
            connection.commit()
            
            # 获取创建的记录
            device_type_id = cursor.lastrowid
            cursor.execute("""
                SELECT dt.*, COALESCE(ip_count.usage_count, 0) as usage_count
                FROM device_types dt
                LEFT JOIN (
                    SELECT device_type, COUNT(*) as usage_count
                    FROM ip_addresses 
                    WHERE device_type IS NOT NULL AND device_type != ''
                    GROUP BY device_type
                ) ip_count ON dt.code = ip_count.device_type
                WHERE dt.id = %s
            """, (device_type_id,))
            result = cursor.fetchone()
            
            return DeviceTypeResponse(
                id=result['id'],
                name=result['name'],
                code=result['code'],
                category=result['category'],
                status=result['status'],
                description=result['description'],
                usage_count=result['usage_count'],
                created_at=str(result['created_at']),
                updated_at=str(result['updated_at']) if result['updated_at'] else None
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create device type: {str(e)}")
    finally:
        connection.close()

@app.put("/api/device-types/{device_type_id}", response_model=DeviceTypeResponse)
async def update_device_type(device_type_id: int, device_type: DeviceTypeUpdate):
    """更新设备类型"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查设备类型是否存在
            cursor.execute("SELECT id FROM device_types WHERE id = %s", (device_type_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="设备类型不存在")
            
            # 如果更新代码，检查是否与其他记录冲突
            if device_type.code:
                cursor.execute("SELECT id FROM device_types WHERE code = %s AND id != %s", 
                             (device_type.code, device_type_id))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="设备类型代码已存在")
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            if device_type.name is not None:
                update_fields.append("name = %s")
                update_values.append(device_type.name)
            
            if device_type.code is not None:
                update_fields.append("code = %s")
                update_values.append(device_type.code)
            
            if device_type.category is not None:
                update_fields.append("category = %s")
                update_values.append(device_type.category)
            
            if device_type.status is not None:
                update_fields.append("status = %s")
                update_values.append(device_type.status)
            
            if device_type.description is not None:
                update_fields.append("description = %s")
                update_values.append(device_type.description)
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="没有提供要更新的字段")
            
            # 添加更新时间和设备类型ID
            update_fields.append("updated_at = NOW()")
            update_values.append(device_type_id)
            
            sql = f"UPDATE device_types SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(sql, update_values)
            connection.commit()
            
            # 获取更新后的记录
            cursor.execute("""
                SELECT dt.*, COALESCE(ip_count.usage_count, 0) as usage_count
                FROM device_types dt
                LEFT JOIN (
                    SELECT device_type, COUNT(*) as usage_count
                    FROM ip_addresses 
                    WHERE device_type IS NOT NULL AND device_type != ''
                    GROUP BY device_type
                ) ip_count ON dt.code = ip_count.device_type
                WHERE dt.id = %s
            """, (device_type_id,))
            result = cursor.fetchone()
            
            return DeviceTypeResponse(
                id=result['id'],
                name=result['name'],
                code=result['code'],
                category=result['category'],
                status=result['status'],
                description=result['description'],
                usage_count=result['usage_count'],
                created_at=str(result['created_at']),
                updated_at=str(result['updated_at']) if result['updated_at'] else None
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update device type: {str(e)}")
    finally:
        connection.close()

@app.delete("/api/device-types/{device_type_id}")
async def delete_device_type(device_type_id: int):
    """删除设备类型"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查设备类型是否存在
            cursor.execute("SELECT code FROM device_types WHERE id = %s", (device_type_id,))
            device_type = cursor.fetchone()
            if not device_type:
                raise HTTPException(status_code=404, detail="设备类型不存在")
            
            # 检查是否有IP地址正在使用此设备类型
            cursor.execute("SELECT COUNT(*) as count FROM ip_addresses WHERE device_type = %s", 
                         (device_type['code'],))
            usage_count = cursor.fetchone()['count']
            
            if usage_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无法删除设备类型，还有 {usage_count} 个IP地址正在使用此类型"
                )
            
            # 删除设备类型
            cursor.execute("DELETE FROM device_types WHERE id = %s", (device_type_id,))
            connection.commit()
            
            return {"message": "设备类型删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete device type: {str(e)}")
    finally:
        connection.close()

@app.patch("/api/device-types/{device_type_id}/status")
async def toggle_device_type_status(device_type_id: int, request: dict):
    """切换设备类型状态"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查设备类型是否存在
            cursor.execute("SELECT id, status FROM device_types WHERE id = %s", (device_type_id,))
            device_type = cursor.fetchone()
            if not device_type:
                raise HTTPException(status_code=404, detail="设备类型不存在")
            
            new_status = request.get('status')
            if new_status not in ['active', 'inactive']:
                raise HTTPException(status_code=400, detail="无效的状态值")
            
            # 更新状态
            cursor.execute(
                "UPDATE device_types SET status = %s, updated_at = NOW() WHERE id = %s",
                (new_status, device_type_id)
            )
            connection.commit()
            
            return {"message": f"设备类型状态已更新为 {new_status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle device type status: {str(e)}")
    finally:
        connection.close()

@app.get("/api/device-types/statistics")
async def get_device_type_statistics():
    """获取设备类型统计信息"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 总数统计
            cursor.execute("SELECT COUNT(*) as total FROM device_types")
            total = cursor.fetchone()['total']
            
            # 状态统计
            cursor.execute("SELECT COUNT(*) as active FROM device_types WHERE status = 'active'")
            active = cursor.fetchone()['active']
            
            cursor.execute("SELECT COUNT(*) as inactive FROM device_types WHERE status = 'inactive'")
            inactive = cursor.fetchone()['inactive']
            
            # 使用统计
            cursor.execute("""
                SELECT COUNT(DISTINCT device_type) as usage_count 
                FROM ip_addresses 
                WHERE device_type IS NOT NULL AND device_type != ''
            """)
            usage_count = cursor.fetchone()['usage_count']
            
            return {
                "total": total,
                "active": active,
                "inactive": inactive,
                "usage_count": usage_count
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device type statistics: {str(e)}")
    finally:
        connection.close()

# 用户角色API端点
@app.get("/api/users/roles/available")
async def get_available_roles():
    """获取可用的用户角色列表"""
    print("=== enhanced_main.py 中的角色API被调用 ===")
    print("=== 强制返回包含只读角色的列表 ===")
    result = [
        {"value": "admin", "label": "管理员", "description": "系统管理员，拥有所有权限"},
        {"value": "manager", "label": "经理", "description": "部门经理，拥有部分管理权限"},
        {"value": "user", "label": "普通用户", "description": "普通用户，拥有基本权限"},
        {"value": "readonly", "label": "只读用户", "description": "只读用户，只能查看IP地址信息"}
    ]
    print(f"=== 返回结果: {result} ===")
    return result

@app.get("/api/users/roles/test")
async def get_roles_test():
    """测试角色API端点"""
    print("=== 测试角色API被调用 ===")
    return [
        {"value": "admin", "label": "管理员", "description": "系统管理员，拥有所有权限"},
        {"value": "manager", "label": "经理", "description": "部门经理，拥有部分管理权限"},
        {"value": "user", "label": "普通用户", "description": "普通用户，拥有基本权限"},
        {"value": "readonly", "label": "只读用户", "description": "只读用户，只能查看IP地址信息"}
    ]

@app.get("/api/users/roles/debug")
async def get_roles_debug():
    """调试角色API端点"""
    print("=== 调试角色API被调用 ===")
    return {
        "message": "这是调试端点",
        "roles": [
            {"value": "admin", "label": "管理员", "description": "系统管理员，拥有所有权限"},
            {"value": "manager", "label": "经理", "description": "部门经理，拥有部分管理权限"},
            {"value": "user", "label": "普通用户", "description": "普通用户，拥有基本权限"},
            {"value": "readonly", "label": "只读用户", "description": "只读用户，只能查看IP地址信息"}
        ]
    }

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