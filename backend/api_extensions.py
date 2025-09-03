"""
API扩展模块 - 添加前端需要的缺失API端点
"""
from fastapi import HTTPException
from typing import List, Optional
import pymysql
import logging

logger = logging.getLogger(__name__)

def add_missing_endpoints(app, get_db_connection):
    """添加缺失的API端点"""
    
    # 网段相关API端点
    @app.get("/api/subnets")
    async def get_subnets_api(skip: int = 0, limit: int = 50):
        """获取网段列表 - /api 路径"""
        return await list_subnets_internal(skip, limit, get_db_connection)
    
    @app.get("/api/subnets/search")
    async def search_subnets_api(q: Optional[str] = None, vlan_id: Optional[int] = None):
        """搜索网段"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where_conditions = []
                params = []
                
                if q:
                    where_conditions.append("(network LIKE %s OR description LIKE %s)")
                    params.extend([f"%{q}%", f"%{q}%"])
                
                if vlan_id:
                    where_conditions.append("vlan_id = %s")
                    params.append(vlan_id)
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                cursor.execute(f"SELECT * FROM subnets WHERE {where_clause}", params)
                results = cursor.fetchall()
                
                return [
                    {
                        "id": row['id'],
                        "network": row['network'],
                        "netmask": row['netmask'],
                        "gateway": row['gateway'],
                        "description": row['description'],
                        "vlan_id": row['vlan_id'],
                        "location": row['location'],
                        "created_at": str(row['created_at'])
                    } for row in results
                ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search subnets: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/subnets/{subnet_id}")
    async def get_subnet_api(subnet_id: int):
        """获取单个网段详情 - /api 路径"""
        return await get_subnet_internal(subnet_id, get_db_connection)
    
    @app.put("/api/subnets/{subnet_id}")
    async def update_subnet_api(subnet_id: int, data: dict):
        """更新网段"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 构建更新字段
                update_fields = []
                update_values = []
                
                for field in ['network', 'netmask', 'gateway', 'description', 'vlan_id', 'location']:
                    if field in data:
                        update_fields.append(f"{field} = %s")
                        update_values.append(data[field])
                
                if not update_fields:
                    raise HTTPException(status_code=400, detail="No fields to update")
                
                update_values.append(subnet_id)
                sql = f"UPDATE subnets SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                
                cursor.execute(sql, update_values)
                connection.commit()
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Subnet not found")
                
                # 返回更新后的网段信息
                return await get_subnet_internal(subnet_id, get_db_connection)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update subnet: {str(e)}")
        finally:
            connection.close()
    
    @app.delete("/api/subnets/{subnet_id}")
    async def delete_subnet_api(subnet_id: int):
        """删除网段"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查是否有关联的IP地址
                cursor.execute("SELECT COUNT(*) as count FROM ip_addresses WHERE subnet_id = %s", (subnet_id,))
                ip_count = cursor.fetchone()['count']
                
                if ip_count > 0:
                    raise HTTPException(status_code=400, detail=f"Cannot delete subnet with {ip_count} IP addresses")
                
                cursor.execute("DELETE FROM subnets WHERE id = %s", (subnet_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Subnet not found")
                
                return {"message": "Subnet deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete subnet: {str(e)}")
        finally:
            connection.close()
    
    # IP地址相关API端点
    @app.get("/api/ips")
    async def get_ips_api(skip: int = 0, limit: int = 50, subnet_id: Optional[int] = None):
        """获取IP地址列表"""
        return await list_ip_addresses_internal(skip, limit, subnet_id, get_db_connection)
    
    @app.get("/api/ips/search")
    async def search_ips_api(skip: int = 0, limit: int = 50, q: Optional[str] = None, 
                            status: Optional[str] = None, subnet_id: Optional[int] = None):
        """搜索IP地址"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where_conditions = []
                params = []
                
                if q:
                    where_conditions.append("(ip_address LIKE %s OR hostname LIKE %s OR assigned_to LIKE %s)")
                    params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
                
                if status:
                    where_conditions.append("status = %s")
                    params.append(status)
                
                if subnet_id:
                    where_conditions.append("subnet_id = %s")
                    params.append(subnet_id)
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                cursor.execute(f"""
                    SELECT * FROM ip_addresses 
                    WHERE {where_clause} 
                    ORDER BY INET_ATON(ip_address) 
                    LIMIT %s OFFSET %s
                """, params + [limit, skip])
                results = cursor.fetchall()
                
                return [
                    {
                        "id": row['id'],
                        "ip_address": row['ip_address'],
                        "subnet_id": row['subnet_id'],
                        "status": row['status'],
                        "hostname": row['hostname'],
                        "mac_address": row['mac_address'],
                        "device_type": row['device_type'],
                        "location": row['location'],
                        "assigned_to": row['assigned_to'],
                        "description": row['description'],
                        "created_at": str(row['created_at'])
                    } for row in results
                ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search IP addresses: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/ips/statistics")
    async def get_ip_statistics_api(subnet_id: Optional[int] = None):
        """获取IP统计信息"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where_clause = "WHERE subnet_id = %s" if subnet_id else ""
                params = [subnet_id] if subnet_id else []
                
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_ips,
                        SUM(CASE WHEN status = 'allocated' THEN 1 ELSE 0 END) as allocated_ips,
                        SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available_ips,
                        SUM(CASE WHEN status = 'reserved' THEN 1 ELSE 0 END) as reserved_ips,
                        SUM(CASE WHEN status = 'conflict' THEN 1 ELSE 0 END) as conflict_ips
                    FROM ip_addresses {where_clause}
                """, params)
                result = cursor.fetchone()
                
                total = result['total_ips'] or 0
                allocated = result['allocated_ips'] or 0
                
                return {
                    "total_ips": total,
                    "allocated_ips": allocated,
                    "available_ips": result['available_ips'] or 0,
                    "reserved_ips": result['reserved_ips'] or 0,
                    "conflict_ips": result['conflict_ips'] or 0,
                    "utilization_rate": round((allocated / total * 100) if total > 0 else 0, 2)
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get IP statistics: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/ips/search-history")
    async def get_search_history_api(limit: int = 20):
        """获取搜索历史（模拟数据）"""
        return []  # 暂时返回空数组
    
    @app.get("/api/ips/search-favorites")
    async def get_search_favorites_api():
        """获取收藏的搜索（模拟数据）"""
        return []  # 暂时返回空数组
    
    # 标签相关API端点
    @app.get("/api/tags/")
    async def get_tags_api(limit: int = 1000):
        """获取标签列表"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM tags LIMIT %s", (limit,))
                results = cursor.fetchall()
                
                return [
                    {
                        "id": row['id'],
                        "name": row['name'],
                        "color": row['color'],
                        "description": row['description'],
                        "created_at": str(row['created_at'])
                    } for row in results
                ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get tags: {str(e)}")
        finally:
            connection.close()
    
    # 自定义字段相关API端点
    @app.get("/api/custom-fields/")
    async def get_custom_fields_api(entity_type: Optional[str] = None):
        """获取自定义字段列表"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                if entity_type:
                    cursor.execute("SELECT * FROM custom_fields WHERE entity_type = %s", (entity_type,))
                else:
                    cursor.execute("SELECT * FROM custom_fields")
                results = cursor.fetchall()
                
                return [
                    {
                        "id": row['id'],
                        "name": row['name'],
                        "field_type": row['field_type'],
                        "entity_type": row['entity_type'],
                        "is_required": bool(row['is_required']),
                        "default_value": row['default_value'],
                        "options": row['options'],
                        "created_at": str(row['created_at'])
                    } for row in results
                ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get custom fields: {str(e)}")
        finally:
            connection.close()
    
    # 用户管理相关API端点
    @app.get("/api/users/")
    async def get_users_api(skip: int = 0, limit: int = 20, active_only: bool = False):
        """获取用户列表"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where_clause = "WHERE is_active = TRUE" if active_only else ""
                cursor.execute(f"""
                    SELECT id, username, email, role, theme, is_active, created_at, updated_at 
                    FROM users {where_clause} 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (limit, skip))
                results = cursor.fetchall()
                
                return [
                    {
                        "id": row['id'],
                        "username": row['username'],
                        "email": row['email'],
                        "role": row['role'],
                        "theme": row['theme'],
                        "is_active": bool(row['is_active']),
                        "created_at": str(row['created_at']),
                        "updated_at": str(row['updated_at']) if row['updated_at'] else None
                    } for row in results
                ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/users/statistics")
    async def get_user_statistics_api():
        """获取用户统计信息"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_users,
                        SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as admin_users,
                        SUM(CASE WHEN role = 'manager' THEN 1 ELSE 0 END) as manager_users,
                        SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as regular_users
                    FROM users
                """)
                result = cursor.fetchone()
                
                return {
                    "total_users": result['total_users'] or 0,
                    "active_users": result['active_users'] or 0,
                    "inactive_users": (result['total_users'] or 0) - (result['active_users'] or 0),
                    "admin_users": result['admin_users'] or 0,
                    "manager_users": result['manager_users'] or 0,
                    "regular_users": result['regular_users'] or 0
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get user statistics: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/users/roles/available")
    async def get_available_roles_api():
        """获取可用角色列表"""
        return [
            {"value": "admin", "label": "管理员", "description": "系统管理员，拥有所有权限"},
            {"value": "manager", "label": "经理", "description": "部门经理，拥有部分管理权限"},
            {"value": "user", "label": "普通用户", "description": "普通用户，拥有基本权限"}
        ]
    
    @app.get("/api/users/themes/available")
    async def get_available_themes_api():
        """获取可用主题列表"""
        return [
            {"value": "light", "label": "明亮主题", "description": "适合白天使用的明亮主题"},
            {"value": "dark", "label": "暗黑主题", "description": "适合夜间使用的暗黑主题"}
        ]

# 内部辅助函数
async def list_subnets_internal(skip: int, limit: int, get_db_connection):
    """内部网段列表函数"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM subnets LIMIT %s OFFSET %s", (limit, skip))
            results = cursor.fetchall()
            
            return [
                {
                    "id": row['id'],
                    "network": row['network'],
                    "netmask": row['netmask'],
                    "gateway": row['gateway'],
                    "description": row['description'],
                    "vlan_id": row['vlan_id'],
                    "location": row['location'],
                    "created_at": str(row['created_at'])
                } for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subnets: {str(e)}")
    finally:
        connection.close()

async def get_subnet_internal(subnet_id: int, get_db_connection):
    """内部获取网段函数"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM subnets WHERE id = %s", (subnet_id,))
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Subnet not found")
            
            return {
                "id": result['id'],
                "network": result['network'],
                "netmask": result['netmask'],
                "gateway": result['gateway'],
                "description": result['description'],
                "vlan_id": result['vlan_id'],
                "location": result['location'],
                "created_at": str(result['created_at'])
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subnet: {str(e)}")
    finally:
        connection.close()

async def list_ip_addresses_internal(skip: int, limit: int, subnet_id: Optional[int], get_db_connection):
    """内部IP地址列表函数"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if subnet_id:
                cursor.execute(
                    "SELECT * FROM ip_addresses WHERE subnet_id = %s ORDER BY INET_ATON(ip_address) LIMIT %s OFFSET %s", 
                    (subnet_id, limit, skip)
                )
            else:
                cursor.execute("SELECT * FROM ip_addresses ORDER BY INET_ATON(ip_address) LIMIT %s OFFSET %s", (limit, skip))
            
            results = cursor.fetchall()
            
            return [
                {
                    "id": row['id'],
                    "ip_address": row['ip_address'],
                    "subnet_id": row['subnet_id'],
                    "status": row['status'],
                    "hostname": row['hostname'],
                    "mac_address": row['mac_address'],
                    "device_type": row['device_type'],
                    "location": row['location'],
                    "assigned_to": row['assigned_to'],
                    "description": row['description'],
                    "created_at": str(row['created_at'])
                } for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch IP addresses: {str(e)}")
    finally:
        connection.close()