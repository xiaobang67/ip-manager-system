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
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 获取总数
                cursor.execute("SELECT COUNT(*) as total FROM subnets")
                total_result = cursor.fetchone()
                total = total_result['total']
                
                # 获取分页数据，包含IP统计信息
                cursor.execute("""
                    SELECT 
                        s.*,
                        COUNT(ip.id) as allocated_count,
                        CASE 
                            WHEN s.netmask REGEXP '^[0-9]+$' THEN 
                                POWER(2, 32 - CAST(s.netmask AS UNSIGNED)) - 2
                            ELSE 
                                CASE s.netmask
                                    WHEN '255.255.255.0' THEN 254
                                    WHEN '255.255.254.0' THEN 510
                                    WHEN '255.255.252.0' THEN 1022
                                    WHEN '255.255.248.0' THEN 2046
                                    WHEN '255.255.240.0' THEN 4094
                                    WHEN '255.255.224.0' THEN 8190
                                    WHEN '255.255.192.0' THEN 16382
                                    WHEN '255.255.128.0' THEN 32766
                                    WHEN '255.255.0.0' THEN 65534
                                    ELSE 254
                                END
                        END as ip_count
                    FROM subnets s
                    LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
                    GROUP BY s.id
                    ORDER BY s.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, skip))
                results = cursor.fetchall()
                
                subnets = []
                for row in results:
                    subnet_data = {
                        "id": row['id'],
                        "network": row['network'],
                        "netmask": row['netmask'],
                        "gateway": row['gateway'],
                        "description": row['description'],
                        "vlan_id": row['vlan_id'],
                        "location": row['location'],
                        "created_at": str(row['created_at']),
                        "allocated_count": int(row['allocated_count'] or 0),
                        "ip_count": int(row['ip_count'] or 0)
                    }
                    subnets.append(subnet_data)
                
                return {
                    "subnets": subnets,
                    "total": total,
                    "page": skip // limit + 1,
                    "size": limit
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch subnets: {str(e)}")
        finally:
            connection.close()
    
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
    
    # IP分配相关端点
    @app.post("/api/ips/allocate")
    async def allocate_ip_api(data: dict):
        """分配IP地址"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 验证必填字段
                subnet_id = data.get('subnet_id')
                if not subnet_id:
                    raise HTTPException(status_code=400, detail="网段ID不能为空")
                
                # 检查网段是否存在
                cursor.execute("SELECT id FROM subnets WHERE id = %s", (subnet_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="网段不存在")
                
                # 如果指定了首选IP，尝试分配
                preferred_ip = data.get('preferred_ip')
                if preferred_ip:
                    cursor.execute("""
                        SELECT id, status FROM ip_addresses 
                        WHERE ip_address = %s AND subnet_id = %s
                    """, (preferred_ip, subnet_id))
                    ip_record = cursor.fetchone()
                    
                    if not ip_record:
                        raise HTTPException(status_code=404, detail=f"IP地址 {preferred_ip} 不存在")
                    
                    if ip_record['status'] != 'available':
                        raise HTTPException(status_code=409, detail=f"IP地址 {preferred_ip} 不可用，当前状态: {ip_record['status']}")
                    
                    ip_id = ip_record['id']
                else:
                    # 自动分配可用IP
                    cursor.execute("""
                        SELECT id, ip_address FROM ip_addresses 
                        WHERE subnet_id = %s AND status = 'available' 
                        ORDER BY INET_ATON(ip_address) 
                        LIMIT 1
                    """, (subnet_id,))
                    ip_record = cursor.fetchone()
                    
                    if not ip_record:
                        raise HTTPException(status_code=404, detail="网段中没有可用的IP地址")
                    
                    ip_id = ip_record['id']
                    preferred_ip = ip_record['ip_address']
                
                # 更新IP地址状态
                cursor.execute("""
                    UPDATE ip_addresses SET 
                        status = 'allocated',
                        mac_address = %s,
                        hostname = %s,
                        device_type = %s,
                        location = %s,
                        assigned_to = %s,
                        description = %s,
                        allocated_at = NOW(),
                        allocated_by = 1,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    data.get('mac_address'),
                    data.get('hostname'),
                    data.get('device_type'),
                    data.get('location'),
                    data.get('assigned_to'),
                    data.get('description'),
                    ip_id
                ))
                
                connection.commit()
                
                # 返回更新后的IP信息
                cursor.execute("SELECT * FROM ip_addresses WHERE id = %s", (ip_id,))
                result = cursor.fetchone()
                
                return {
                    "id": result['id'],
                    "ip_address": result['ip_address'],
                    "subnet_id": result['subnet_id'],
                    "status": result['status'],
                    "hostname": result['hostname'],
                    "mac_address": result['mac_address'],
                    "device_type": result['device_type'],
                    "location": result['location'],
                    "assigned_to": result['assigned_to'],
                    "description": result['description'],
                    "allocated_at": str(result['allocated_at']) if result['allocated_at'] else None,
                    "allocated_by": result['allocated_by'],
                    "created_at": str(result['created_at']),
                    "updated_at": str(result['updated_at'])
                }
                
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"分配IP地址失败: {str(e)}")
        finally:
            connection.close()
    
    @app.post("/api/ips/reserve")
    async def reserve_ip_api(data: dict):
        """保留IP地址"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                ip_address = data.get('ip_address')
                reason = data.get('reason')
                
                if not ip_address:
                    raise HTTPException(status_code=400, detail="IP地址不能为空")
                if not reason:
                    raise HTTPException(status_code=400, detail="保留原因不能为空")
                
                # 查找IP记录
                cursor.execute("SELECT id, status FROM ip_addresses WHERE ip_address = %s", (ip_address,))
                ip_record = cursor.fetchone()
                
                if not ip_record:
                    raise HTTPException(status_code=404, detail=f"IP地址 {ip_address} 不存在")
                
                if ip_record['status'] != 'available':
                    raise HTTPException(status_code=409, detail=f"IP地址 {ip_address} 不可用，当前状态: {ip_record['status']}")
                
                # 更新IP状态为保留
                cursor.execute("""
                    UPDATE ip_addresses SET 
                        status = 'reserved',
                        description = %s,
                        assigned_to = %s,
                        allocated_at = NOW(),
                        allocated_by = 1,
                        updated_at = NOW()
                    WHERE id = %s
                """, (reason, f"保留 - {reason}", ip_record['id']))
                
                connection.commit()
                
                # 返回更新后的IP信息
                cursor.execute("SELECT * FROM ip_addresses WHERE id = %s", (ip_record['id'],))
                result = cursor.fetchone()
                
                return {
                    "id": result['id'],
                    "ip_address": result['ip_address'],
                    "subnet_id": result['subnet_id'],
                    "status": result['status'],
                    "hostname": result['hostname'],
                    "mac_address": result['mac_address'],
                    "device_type": result['device_type'],
                    "location": result['location'],
                    "assigned_to": result['assigned_to'],
                    "description": result['description'],
                    "allocated_at": str(result['allocated_at']) if result['allocated_at'] else None,
                    "allocated_by": result['allocated_by'],
                    "created_at": str(result['created_at']),
                    "updated_at": str(result['updated_at'])
                }
                
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"保留IP地址失败: {str(e)}")
        finally:
            connection.close()
    
    @app.post("/api/ips/release")
    async def release_ip_api(data: dict):
        """释放IP地址"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                ip_address = data.get('ip_address')
                reason = data.get('reason')
                
                if not ip_address:
                    raise HTTPException(status_code=400, detail="IP地址不能为空")
                
                # 查找IP记录
                cursor.execute("SELECT id, status FROM ip_addresses WHERE ip_address = %s", (ip_address,))
                ip_record = cursor.fetchone()
                
                if not ip_record:
                    raise HTTPException(status_code=404, detail=f"IP地址 {ip_address} 不存在")
                
                if ip_record['status'] not in ['allocated', 'reserved']:
                    raise HTTPException(status_code=400, detail=f"IP地址 {ip_address} 无法释放，当前状态: {ip_record['status']}")
                
                # 更新IP状态为可用
                cursor.execute("""
                    UPDATE ip_addresses SET 
                        status = 'available',
                        mac_address = NULL,
                        hostname = NULL,
                        device_type = NULL,
                        location = NULL,
                        assigned_to = NULL,
                        description = %s,
                        allocated_at = NULL,
                        allocated_by = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                """, (reason, ip_record['id']))
                
                connection.commit()
                
                # 返回更新后的IP信息
                cursor.execute("SELECT * FROM ip_addresses WHERE id = %s", (ip_record['id'],))
                result = cursor.fetchone()
                
                return {
                    "id": result['id'],
                    "ip_address": result['ip_address'],
                    "subnet_id": result['subnet_id'],
                    "status": result['status'],
                    "hostname": result['hostname'],
                    "mac_address": result['mac_address'],
                    "device_type": result['device_type'],
                    "location": result['location'],
                    "assigned_to": result['assigned_to'],
                    "description": result['description'],
                    "allocated_at": str(result['allocated_at']) if result['allocated_at'] else None,
                    "allocated_by": result['allocated_by'],
                    "created_at": str(result['created_at']),
                    "updated_at": str(result['updated_at'])
                }
                
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"释放IP地址失败: {str(e)}")
        finally:
            connection.close()
    
    @app.post("/api/ips/bulk-operation")
    async def bulk_ip_operation_api(data: dict):
        """批量IP地址操作"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                ip_addresses = data.get('ip_addresses', [])
                operation = data.get('operation')
                reason = data.get('reason', '')
                
                if not ip_addresses:
                    raise HTTPException(status_code=400, detail="请选择要操作的IP地址")
                
                if operation not in ['reserve', 'release']:
                    raise HTTPException(status_code=400, detail="无效的操作类型")
                
                success_ips = []
                failed_ips = []
                
                for ip_address in ip_addresses:
                    try:
                        # 查找IP记录
                        cursor.execute("SELECT id, status FROM ip_addresses WHERE ip_address = %s", (ip_address,))
                        ip_record = cursor.fetchone()
                        
                        if not ip_record:
                            failed_ips.append({"ip": ip_address, "error": "IP地址不存在"})
                            continue
                        
                        if operation == 'reserve':
                            if ip_record['status'] != 'available':
                                failed_ips.append({"ip": ip_address, "error": f"IP不可用，当前状态: {ip_record['status']}"})
                                continue
                            
                            cursor.execute("""
                                UPDATE ip_addresses SET 
                                    status = 'reserved',
                                    description = %s,
                                    assigned_to = %s,
                                    allocated_at = NOW(),
                                    allocated_by = 1,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (reason, f"批量保留 - {reason}", ip_record['id']))
                            
                        elif operation == 'release':
                            if ip_record['status'] not in ['allocated', 'reserved']:
                                failed_ips.append({"ip": ip_address, "error": f"IP无法释放，当前状态: {ip_record['status']}"})
                                continue
                            
                            cursor.execute("""
                                UPDATE ip_addresses SET 
                                    status = 'available',
                                    mac_address = NULL,
                                    hostname = NULL,
                                    device_type = NULL,
                                    location = NULL,
                                    assigned_to = NULL,
                                    description = %s,
                                    allocated_at = NULL,
                                    allocated_by = NULL,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (reason, ip_record['id']))
                        
                        success_ips.append(ip_address)
                        
                    except Exception as e:
                        failed_ips.append({"ip": ip_address, "error": str(e)})
                
                connection.commit()
                
                return {
                    "success_count": len(success_ips),
                    "failed_count": len(failed_ips),
                    "success_ips": success_ips,
                    "failed_ips": failed_ips,
                    "message": f"批量操作完成：成功{len(success_ips)}个，失败{len(failed_ips)}个"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/ips/{ip_address}/history")
    async def get_ip_history_api(ip_address: str):
        """获取IP地址历史记录"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 首先验证IP地址是否存在
                cursor.execute("SELECT id FROM ip_addresses WHERE ip_address = %s", (ip_address,))
                ip_record = cursor.fetchone()
                
                if not ip_record:
                    raise HTTPException(status_code=404, detail=f"IP地址 {ip_address} 不存在")
                
                # 查询审计日志（如果存在）
                cursor.execute("""
                    SELECT 
                        action,
                        old_values,
                        new_values,
                        created_at,
                        'system' as username
                    FROM audit_logs 
                    WHERE entity_type = 'ip' AND entity_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 50
                """, (ip_record['id'],))
                
                results = cursor.fetchall()
                
                return [
                    {
                        "action": row['action'],
                        "username": row['username'],
                        "old_values": row['old_values'],
                        "new_values": row['new_values'],
                        "created_at": str(row['created_at'])
                    } for row in results
                ]
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取IP历史记录失败: {str(e)}")
        finally:
            connection.close()
    
    @app.post("/api/ips/advanced-search")
    async def advanced_search_ips_api(data: dict):
        """高级搜索IP地址"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 构建查询条件
                where_conditions = []
                params = []
                
                # 基本搜索
                if data.get('query'):
                    where_conditions.append("(ip_address LIKE %s OR hostname LIKE %s OR assigned_to LIKE %s)")
                    query_param = f"%{data['query']}%"
                    params.extend([query_param, query_param, query_param])
                
                # 网段过滤
                if data.get('subnet_id'):
                    where_conditions.append("subnet_id = %s")
                    params.append(data['subnet_id'])
                
                # 状态过滤
                if data.get('status'):
                    where_conditions.append("status = %s")
                    params.append(data['status'])
                
                # 设备类型过滤
                if data.get('device_type'):
                    where_conditions.append("device_type = %s")
                    params.append(data['device_type'])
                
                # 位置过滤
                if data.get('location'):
                    where_conditions.append("location LIKE %s")
                    params.append(f"%{data['location']}%")
                
                # 分配给过滤
                if data.get('assigned_to'):
                    where_conditions.append("assigned_to LIKE %s")
                    params.append(f"%{data['assigned_to']}%")
                
                # MAC地址过滤
                if data.get('mac_address'):
                    where_conditions.append("mac_address LIKE %s")
                    params.append(f"%{data['mac_address']}%")
                
                # 主机名过滤
                if data.get('hostname'):
                    where_conditions.append("hostname LIKE %s")
                    params.append(f"%{data['hostname']}%")
                
                # IP范围过滤
                if data.get('ip_range_start') and data.get('ip_range_end'):
                    where_conditions.append("INET_ATON(ip_address) BETWEEN INET_ATON(%s) AND INET_ATON(%s)")
                    params.extend([data['ip_range_start'], data['ip_range_end']])
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # 分页参数
                skip = data.get('skip', 0)
                limit = data.get('limit', 50)
                
                # 获取总数
                count_query = f"SELECT COUNT(*) as total FROM ip_addresses WHERE {where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()['total']
                
                # 获取数据
                data_query = f"""
                    SELECT * FROM ip_addresses 
                    WHERE {where_clause} 
                    ORDER BY INET_ATON(ip_address) 
                    LIMIT %s OFFSET %s
                """
                cursor.execute(data_query, params + [limit, skip])
                results = cursor.fetchall()
                
                # 计算分页信息
                page = (skip // limit) + 1 if limit > 0 else 1
                total_pages = (total + limit - 1) // limit if limit > 0 else 1
                
                items = [
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
                        "allocated_at": str(row['allocated_at']) if row['allocated_at'] else None,
                        "allocated_by": row['allocated_by'],
                        "created_at": str(row['created_at']),
                        "updated_at": str(row['updated_at'])
                    } for row in results
                ]
                
                return {
                    "items": items,
                    "total": total,
                    "page": page,
                    "page_size": limit,
                    "total_pages": total_pages
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"高级搜索失败: {str(e)}")
        finally:
            connection.close()
    
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
                        "field_name": row['field_name'],
                        "field_type": row['field_type'],
                        "entity_type": row['entity_type'],
                        "is_required": bool(row['is_required']),
                        "field_options": row['field_options'],
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