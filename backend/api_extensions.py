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
    
    # 部门管理API端点
    @app.get("/api/departments/")
    async def get_departments_fallback(skip: int = 0, limit: int = 50, search: str = None):
        """获取部门列表 - 备用端点"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where_conditions = []
                params = []
                
                if search:
                    where_conditions.append("(name LIKE %s OR code LIKE %s)")
                    params.extend([f"%{search}%", f"%{search}%"])
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # 获取总数
                cursor.execute(f"SELECT COUNT(*) as total FROM departments WHERE {where_clause}", params)
                total_result = cursor.fetchone()
                total = total_result['total'] if total_result else 0
                
                # 获取分页数据
                cursor.execute(f"""
                    SELECT * FROM departments 
                    WHERE {where_clause} 
                    ORDER BY name 
                    LIMIT %s OFFSET %s
                """, params + [limit, skip])
                results = cursor.fetchall()
                
                departments = []
                for row in results:
                    departments.append({
                        "id": row['id'],
                        "name": row['name'],
                        "code": row['code'],
                        "created_at": str(row['created_at']) if row['created_at'] else None
                    })
                
                return {
                    "departments": departments,
                    "total": total,
                    "skip": skip,
                    "limit": limit
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch departments: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/departments/statistics")
    async def get_department_statistics_fallback():
        """获取部门统计信息 - 备用端点"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as total FROM departments")
                total_result = cursor.fetchone()
                total = total_result['total'] if total_result else 0
                
                return {
                    "total_departments": total
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch department statistics: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/departments/options")
    async def get_department_options_fallback():
        """获取部门选项列表 - 备用端点"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, name, code FROM departments ORDER BY name")
                results = cursor.fetchall()
                
                departments = []
                for row in results:
                    departments.append({
                        "id": row['id'],
                        "name": row['name'],
                        "code": row['code']
                    })
                
                return {"departments": departments}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch department options: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/departments/{department_id}")
    async def get_department_fallback(department_id: int):
        """获取部门详情 - 备用端点"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM departments WHERE id = %s", (department_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise HTTPException(status_code=404, detail="部门不存在")
                
                return {
                    "id": result['id'],
                    "name": result['name'],
                    "code": result['code'],
                    "created_at": str(result['created_at']) if result['created_at'] else None
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch department: {str(e)}")
        finally:
            connection.close()
    
    @app.post("/api/departments/")
    async def create_department_fallback(data: dict):
        """创建部门 - 备用端点"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 验证必填字段
                name = data.get('name')
                if not name or not name.strip():
                    raise HTTPException(status_code=400, detail="部门名称不能为空")
                
                # 检查名称是否已存在
                cursor.execute("SELECT id FROM departments WHERE name = %s", (name.strip(),))
                if cursor.fetchone():
                    raise HTTPException(status_code=409, detail=f"部门名称 '{name}' 已存在")
                
                # 检查编码是否已存在（如果提供了编码）
                code = data.get('code')
                if code and code.strip():
                    cursor.execute("SELECT id FROM departments WHERE code = %s", (code.strip(),))
                    if cursor.fetchone():
                        raise HTTPException(status_code=409, detail=f"部门编码 '{code}' 已存在")
                
                # 插入新部门
                cursor.execute("""
                    INSERT INTO departments (name, code, created_at)
                    VALUES (%s, %s, NOW())
                """, (
                    name.strip(),
                    code.strip() if code else None
                ))
                
                department_id = cursor.lastrowid
                connection.commit()
                
                # 返回创建的部门信息
                cursor.execute("SELECT * FROM departments WHERE id = %s", (department_id,))
                result = cursor.fetchone()
                
                return {
                    "id": result['id'],
                    "name": result['name'],
                    "code": result['code'],
                    "created_at": str(result['created_at']) if result['created_at'] else None
                }
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create department: {str(e)}")
        finally:
            connection.close()
    
    @app.put("/api/departments/{department_id}")
    async def update_department_fallback(department_id: int, data: dict):
        """更新部门 - 备用端点"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查部门是否存在
                cursor.execute("SELECT * FROM departments WHERE id = %s", (department_id,))
                existing = cursor.fetchone()
                if not existing:
                    raise HTTPException(status_code=404, detail="部门不存在")
                
                # 构建更新字段
                update_fields = []
                update_values = []
                
                if 'name' in data:
                    name = data['name'].strip() if data['name'] else None
                    if not name:
                        raise HTTPException(status_code=400, detail="部门名称不能为空")
                    
                    # 检查名称冲突
                    if name != existing['name']:
                        cursor.execute("SELECT id FROM departments WHERE name = %s AND id != %s", (name, department_id))
                        if cursor.fetchone():
                            raise HTTPException(status_code=409, detail=f"部门名称 '{name}' 已存在")
                    
                    update_fields.append("name = %s")
                    update_values.append(name)
                
                if 'code' in data:
                    code = data['code'].strip() if data['code'] else None
                    
                    # 检查编码冲突
                    if code and code != existing['code']:
                        cursor.execute("SELECT id FROM departments WHERE code = %s AND id != %s", (code, department_id))
                        if cursor.fetchone():
                            raise HTTPException(status_code=409, detail=f"部门编码 '{code}' 已存在")
                    
                    update_fields.append("code = %s")
                    update_values.append(code)
                
                if not update_fields:
                    raise HTTPException(status_code=400, detail="没有提供要更新的字段")
                
                update_values.append(department_id)
                
                # 执行更新
                sql = f"UPDATE departments SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(sql, update_values)
                connection.commit()
                
                # 返回更新后的部门信息
                cursor.execute("SELECT * FROM departments WHERE id = %s", (department_id,))
                result = cursor.fetchone()
                
                return {
                    "id": result['id'],
                    "name": result['name'],
                    "code": result['code'],
                    "created_at": str(result['created_at']) if result['created_at'] else None
                }
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update department: {str(e)}")
        finally:
            connection.close()
    
    @app.delete("/api/departments/{department_id}")
    async def delete_department_fallback(department_id: int):
        """删除部门 - 备用端点"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查部门是否存在
                cursor.execute("SELECT name FROM departments WHERE id = %s", (department_id,))
                existing = cursor.fetchone()
                if not existing:
                    raise HTTPException(status_code=404, detail="部门不存在")
                
                # 这里可以添加检查是否有关联的用户等
                # 暂时直接删除
                
                cursor.execute("DELETE FROM departments WHERE id = %s", (department_id,))
                connection.commit()
                
                return {"message": "部门删除成功"}
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete department: {str(e)}")
        finally:
            connection.close()
    
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
                        COUNT(CASE WHEN ip.status = 'allocated' THEN 1 END) as allocated_count,
                        COUNT(CASE WHEN ip.status = 'available' THEN 1 END) as available_count
                    FROM subnets s
                    LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
                    GROUP BY s.id
                    ORDER BY s.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, skip))
                results = cursor.fetchall()
                
                subnets = []
                for row in results:
                    # 使用Python的ipaddress库计算正确的IP总数
                    import ipaddress
                    try:
                        network = ipaddress.ip_network(row['network'], strict=False)
                        total_ips = network.num_addresses - 2  # 排除网络地址和广播地址
                    except ValueError:
                        # 如果网段格式错误，使用数据库中的IP数量作为备选
                        total_ips = (row['allocated_count'] or 0) + (row['available_count'] or 0)
                    
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
                        "available_count": int(row['available_count'] or 0),
                        "ip_count": total_ips
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
    
    @app.post("/api/subnets/{subnet_id}/sync-ips")
    async def sync_subnet_ips_api(subnet_id: int):
        """同步网段的IP地址列表 - 根据CIDR重新生成正确的IP地址范围"""
        connection = get_db_connection()
        try:
            import ipaddress
            
            with connection.cursor() as cursor:
                # 检查网段是否存在
                cursor.execute("SELECT network FROM subnets WHERE id = %s", (subnet_id,))
                subnet_result = cursor.fetchone()
                if not subnet_result:
                    raise HTTPException(status_code=404, detail="网段不存在")
                
                network = subnet_result['network']
                
                # 解析网段
                try:
                    net = ipaddress.ip_network(network, strict=False)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"无效的网段格式: {network}")
                
                # 获取当前网段中的所有IP地址
                cursor.execute(
                    "SELECT ip_address, status FROM ip_addresses WHERE subnet_id = %s",
                    (subnet_id,)
                )
                existing_ips = cursor.fetchall()
                existing_ip_dict = {ip['ip_address']: ip['status'] for ip in existing_ips}
                
                # 生成网段中应该存在的所有IP地址
                expected_ips = {str(ip) for ip in net.hosts()}
                
                # 找出需要添加和删除的IP地址
                existing_ip_set = set(existing_ip_dict.keys())
                ips_to_add = expected_ips - existing_ip_set
                ips_to_remove = existing_ip_set - expected_ips
                
                stats = {
                    'added': 0,
                    'removed': 0,
                    'kept': len(existing_ip_set & expected_ips)
                }
                
                # 删除不再属于网段的IP地址（只删除未分配的）
                if ips_to_remove:
                    for ip_to_remove in ips_to_remove:
                        if existing_ip_dict[ip_to_remove] == 'available':
                            cursor.execute(
                                "DELETE FROM ip_addresses WHERE subnet_id = %s AND ip_address = %s",
                                (subnet_id, ip_to_remove)
                            )
                            stats['removed'] += 1
                
                # 添加新的IP地址
                if ips_to_add:
                    for ip_str in ips_to_add:
                        cursor.execute(
                            "INSERT INTO ip_addresses (ip_address, subnet_id, status) VALUES (%s, %s, 'available')",
                            (ip_str, subnet_id)
                        )
                    stats['added'] = len(ips_to_add)
                
                connection.commit()
                
                return {
                    "message": "IP地址同步完成",
                    "subnet_id": subnet_id,
                    "network": network,
                    "stats": stats
                }
        except Exception as e:
            connection.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
        finally:
            connection.close()
    
    # IP地址相关API端点
    @app.get("/api/ips")
    async def get_ips_api(skip: int = 0, limit: int = 50, subnet_id: Optional[int] = None):
        """获取IP地址列表"""
        return await list_ip_addresses_internal(skip, limit, subnet_id, get_db_connection)
    
    @app.get("/api/ips/search")
    async def search_ips_api(skip: int = 0, limit: int = 50, query: Optional[str] = None, 
                            status: Optional[str] = None, subnet_id: Optional[int] = None,
                            assigned_to: Optional[str] = None):
        """搜索IP地址"""
        print(f"搜索参数: query={query}, status={status}, subnet_id={subnet_id}, assigned_to={assigned_to}, skip={skip}, limit={limit}")  # 调试信息
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where_conditions = []
                params = []
                
                # 处理assigned_to参数（精确匹配）
                if assigned_to:
                    where_conditions.append("assigned_to = %s")
                    params.append(assigned_to)
                
                if query:
                    # 智能搜索：检测查询类型
                    import re
                    
                    # 检查是否是完整的IP地址格式
                    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                    if re.match(ip_pattern, query):
                        # 完整IP地址：只进行精确匹配
                        where_conditions.append("ip_address = %s")
                        params.append(query)
                    else:
                        # 其他情况：进行模糊匹配，但对assigned_to优先精确匹配
                        where_conditions.append("""(
                            ip_address LIKE %s OR 
                            user_name LIKE %s OR 
                            assigned_to = %s OR
                            assigned_to LIKE %s OR
                            mac_address LIKE %s OR
                            description LIKE %s
                        )""")
                        params.extend([f"%{query}%", f"%{query}%", query, f"%{query}%", f"%{query}%", f"%{query}%"])
                
                if status:
                    where_conditions.append("status = %s")
                    params.append(status)
                
                if subnet_id:
                    where_conditions.append("subnet_id = %s")
                    params.append(subnet_id)
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # 首先获取总数
                cursor.execute(f"""
                    SELECT COUNT(*) as total FROM ip_addresses 
                    WHERE {where_clause}
                """, params)
                total_count = cursor.fetchone()['total']
                
                # 然后获取分页数据
                cursor.execute(f"""
                    SELECT * FROM ip_addresses 
                    WHERE {where_clause} 
                    ORDER BY INET_ATON(ip_address) 
                    LIMIT %s OFFSET %s
                """, params + [limit, skip])
                results = cursor.fetchall()
                
                data = [
                    {
                        "id": row['id'],
                        "ip_address": row['ip_address'],
                        "subnet_id": row['subnet_id'],
                        "status": row['status'],
                        "user_name": row['user_name'],
                        "mac_address": row['mac_address'],
                        "device_type": row['device_type'],
                        "location": row['location'],
                        "assigned_to": row['assigned_to'],
                        "description": row['description'],
                        "allocated_at": str(row['allocated_at']) if row['allocated_at'] else None,
                        "created_at": str(row['created_at'])
                    } for row in results
                ]
                
                return {
                    "data": data,
                    "total": total_count,
                    "skip": skip,
                    "limit": limit
                }
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
                        user_name = %s,
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
                    data.get('user_name'),  # 改为user_name
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
                    "user_name": result['user_name'],
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
                    "user_name": result['user_name'],
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
                        user_name = NULL,
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
                    "user_name": result['user_name'],
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
                
                if operation not in ['reserve', 'release', 'delete']:
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
                                    user_name = NULL,
                                    device_type = NULL,
                                    location = NULL,
                                    assigned_to = NULL,
                                    description = %s,
                                    allocated_at = NULL,
                                    allocated_by = NULL,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (reason, ip_record['id']))
                            
                        elif operation == 'delete':
                            if ip_record['status'] == 'allocated':
                                failed_ips.append({"ip": ip_address, "error": "IP已分配，无法删除。请先释放该IP地址"})
                                continue
                            
                            cursor.execute("DELETE FROM ip_addresses WHERE id = %s", (ip_record['id'],))
                        
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
    
    @app.delete("/api/ips/delete")
    async def delete_ip_api(data: dict):
        """删除IP地址"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                ip_address = data.get('ip_address')
                reason = data.get('reason', '')
                
                if not ip_address:
                    raise HTTPException(status_code=400, detail="IP地址不能为空")
                
                # 查找IP记录
                cursor.execute("SELECT id, status FROM ip_addresses WHERE ip_address = %s", (ip_address,))
                ip_record = cursor.fetchone()
                
                if not ip_record:
                    raise HTTPException(status_code=404, detail=f"IP地址 {ip_address} 不存在")
                
                # 检查IP地址是否可以删除
                if ip_record['status'] == 'allocated':
                    raise HTTPException(status_code=400, detail=f"IP地址 {ip_address} 已分配，无法删除。请先释放该IP地址")
                
                # 删除IP地址记录
                cursor.execute("DELETE FROM ip_addresses WHERE id = %s", (ip_record['id'],))
                connection.commit()
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=500, detail=f"删除IP地址 {ip_address} 失败")
                
                return {
                    "ip_address": ip_address,
                    "message": f"IP地址 {ip_address} 删除成功",
                    "reason": reason
                }
                
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"删除IP地址失败: {str(e)}")
        finally:
            connection.close()

    @app.put("/api/ips/{ip_address}")
    async def update_ip_api(ip_address: str, data: dict):
        """更新IP地址信息"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 首先验证IP地址是否存在
                cursor.execute("SELECT id FROM ip_addresses WHERE ip_address = %s", (ip_address,))
                ip_record = cursor.fetchone()
                
                if not ip_record:
                    raise HTTPException(status_code=404, detail=f"IP地址 {ip_address} 不存在")
                
                # 准备更新字段
                update_fields = []
                update_values = []
                
                # 可更新的字段列表
                updatable_fields = {
                    'mac_address': 'mac_address',
                    'user_name': 'user_name', 
                    'device_type': 'device_type',
                    'assigned_to': 'assigned_to',
                    'description': 'description',
                    'allocated_at': 'allocated_at'
                }
                
                for field_name, db_column in updatable_fields.items():
                    if field_name in data:
                        update_fields.append(f"{db_column} = %s")
                        update_values.append(data[field_name])
                
                if not update_fields:
                    raise HTTPException(status_code=400, detail="没有提供要更新的字段")
                
                # 添加更新时间
                update_fields.append("updated_at = NOW()")
                
                # 构建更新SQL
                update_sql = f"""
                    UPDATE ip_addresses 
                    SET {', '.join(update_fields)}
                    WHERE ip_address = %s
                """
                update_values.append(ip_address)
                
                # 执行更新
                cursor.execute(update_sql, update_values)
                connection.commit()
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"IP地址 {ip_address} 更新失败")
                
                # 记录审计日志
                try:
                    cursor.execute("""
                        INSERT INTO audit_logs (action, resource_type, resource_id, username, details, created_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """, (
                        'update',
                        'ip_address', 
                        ip_record['id'],
                        data.get('username', 'system'),
                        f"更新IP地址 {ip_address} 的信息"
                    ))
                    connection.commit()
                except Exception as audit_error:
                    print(f"审计日志记录失败: {audit_error}")
                    # 审计日志失败不影响主要操作
                
                return {"message": f"IP地址 {ip_address} 更新成功"}
                
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"更新IP地址失败: {str(e)}")
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
                    where_conditions.append("(ip_address LIKE %s OR user_name LIKE %s OR assigned_to LIKE %s)")
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
                
                # 使用人过滤
                if data.get('user_name'):
                    where_conditions.append("user_name LIKE %s")
                    params.append(f"%{data['user_name']}%")
                
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

    # 网段验证端点
    @app.post("/api/subnets/validate")
    async def validate_subnet_api(data: dict):
        """验证网段格式和重叠检测"""
        connection = get_db_connection()
        try:
            network = data.get('network')
            exclude_id = data.get('exclude_id')
            
            if not network:
                return {
                    "is_valid": False,
                    "message": "网段地址不能为空"
                }
            
            # 验证CIDR格式
            try:
                import ipaddress
                ipaddress.ip_network(network, strict=False)
            except ValueError:
                return {
                    "is_valid": False,
                    "message": "无效的网段格式，请使用CIDR格式如192.168.1.0/24"
                }
            
            with connection.cursor() as cursor:
                # 简化的重叠检查 - 只检查网段地址是否已存在
                if exclude_id:
                    cursor.execute("""
                        SELECT id, network, description FROM subnets 
                        WHERE id != %s AND network = %s
                    """, (exclude_id, network))
                else:
                    cursor.execute("""
                        SELECT id, network, description FROM subnets 
                        WHERE network = %s
                    """, (network,))
                
                overlapping_subnets = cursor.fetchall()
                
                if overlapping_subnets:
                    return {
                        "is_valid": False,
                        "message": f"网段与 {len(overlapping_subnets)} 个现有网段重叠",
                        "overlapping_subnets": [
                            {
                                "id": row['id'],
                                "network": row['network'],
                                "description": row['description']
                            } for row in overlapping_subnets
                        ]
                    }
                
                return {
                    "is_valid": True,
                    "message": "网段验证通过"
                }
                
        except Exception as e:
            return {
                "is_valid": False,
                "message": f"验证失败: {str(e)}"
            }
        finally:
            connection.close()
    
    # 用户管理API端点
    @app.get("/api/users")
    @app.get("/api/users/")
    async def get_users_api(skip: int = 0, limit: int = 20, active_only: bool = False):
        """获取用户列表"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 构建查询条件
                where_clause = "WHERE is_active = TRUE" if active_only else ""
                
                # 获取总数
                cursor.execute(f"SELECT COUNT(*) as total FROM users {where_clause}")
                total = cursor.fetchone()['total']
                
                # 获取用户列表
                cursor.execute(f"""
                    SELECT id, username, email, role, theme, is_active, created_at, updated_at 
                    FROM users {where_clause}
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (limit, skip))
                results = cursor.fetchall()
                
                users = []
                for row in results:
                    users.append({
                        "id": row['id'],
                        "username": row['username'],
                        "email": row['email'],
                        "role": row['role'],
                        "theme": row['theme'],
                        "is_active": bool(row['is_active']),
                        "created_at": str(row['created_at']) if row['created_at'] else None,
                        "updated_at": str(row['updated_at']) if row['updated_at'] else None
                    })
                
                return {
                    "users": users,
                    "total": total,
                    "skip": skip,
                    "limit": limit
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/users/statistics")
    async def get_user_statistics_api():
        """获取用户统计信息"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 总用户数
                cursor.execute("SELECT COUNT(*) as total FROM users")
                total_users = cursor.fetchone()['total']
                
                # 活跃用户数
                cursor.execute("SELECT COUNT(*) as active FROM users WHERE is_active = TRUE")
                active_users = cursor.fetchone()['active']
                
                # 按角色统计
                cursor.execute("""
                    SELECT role, COUNT(*) as count 
                    FROM users 
                    GROUP BY role
                """)
                role_results = cursor.fetchall()
                
                role_distribution = {}
                for row in role_results:
                    role_distribution[row['role']] = row['count']
                
                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "inactive_users": total_users - active_users,
                    "role_distribution": role_distribution
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")
        finally:
            connection.close()
    
    @app.get("/api/users/roles/available")
    async def get_available_roles_api():
        """获取可用的用户角色列表"""
        return {
            "roles": [
                {"value": "admin", "label": "管理员"},
                {"value": "manager", "label": "经理"},
                {"value": "user", "label": "普通用户"}
            ]
        }
    
    @app.get("/api/users/themes/available")
    async def get_available_themes_api():
        """获取可用的主题列表"""
        return {
            "themes": [
                {"value": "light", "label": "明亮主题"},
                {"value": "dark", "label": "暗黑主题"}
            ]
        }
    
    @app.get("/api/users/{user_id}")
    async def get_user_api(user_id: int):
        """获取用户详情"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, username, email, role, theme, is_active, created_at, updated_at 
                    FROM users WHERE id = %s
                """, (user_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                return {
                    "id": result['id'],
                    "username": result['username'],
                    "email": result['email'],
                    "role": result['role'],
                    "theme": result['theme'],
                    "is_active": bool(result['is_active']),
                    "created_at": str(result['created_at']) if result['created_at'] else None,
                    "updated_at": str(result['updated_at']) if result['updated_at'] else None
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")
        finally:
            connection.close()
    
    @app.post("/api/users")
    @app.post("/api/users/")
    async def create_user_api(data: dict):
        """创建新用户"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                username = data.get('username')
                password = data.get('password')
                email = data.get('email')
                role = data.get('role', 'user')
                
                if not username or not password:
                    raise HTTPException(status_code=400, detail="用户名和密码不能为空")
                
                # 检查用户名是否已存在
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="用户名已存在")
                
                # 检查邮箱是否已存在
                if email:
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if cursor.fetchone():
                        raise HTTPException(status_code=400, detail="邮箱地址已存在")
                
                # 创建用户（简单的密码哈希，生产环境应使用bcrypt）
                import hashlib
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute("""
                    INSERT INTO users (username, password_hash, email, role, theme, is_active, created_at)
                    VALUES (%s, %s, %s, %s, 'light', TRUE, NOW())
                """, (username, password_hash, email, role))
                
                connection.commit()
                user_id = cursor.lastrowid
                
                # 返回创建的用户信息
                cursor.execute("""
                    SELECT id, username, email, role, theme, is_active, created_at 
                    FROM users WHERE id = %s
                """, (user_id,))
                result = cursor.fetchone()
                
                return {
                    "id": result['id'],
                    "username": result['username'],
                    "email": result['email'],
                    "role": result['role'],
                    "theme": result['theme'],
                    "is_active": bool(result['is_active']),
                    "created_at": str(result['created_at'])
                }
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")
        finally:
            connection.close()
    
    @app.put("/api/users/{user_id}")
    async def update_user_api(user_id: int, data: dict):
        """更新用户信息"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查用户是否存在
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                # 构建更新字段
                update_fields = []
                update_values = []
                
                for field in ['username', 'email', 'role', 'theme', 'is_active']:
                    if field in data:
                        # 检查用户名和邮箱的唯一性
                        if field == 'username':
                            cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (data[field], user_id))
                            if cursor.fetchone():
                                raise HTTPException(status_code=400, detail="用户名已存在")
                        elif field == 'email' and data[field]:
                            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (data[field], user_id))
                            if cursor.fetchone():
                                raise HTTPException(status_code=400, detail="邮箱地址已存在")
                        
                        update_fields.append(f"{field} = %s")
                        update_values.append(data[field])
                
                if not update_fields:
                    raise HTTPException(status_code=400, detail="没有提供要更新的字段")
                
                update_values.append(user_id)
                sql = f"UPDATE users SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
                
                cursor.execute(sql, update_values)
                connection.commit()
                
                # 返回更新后的用户信息
                cursor.execute("""
                    SELECT id, username, email, role, theme, is_active, created_at, updated_at 
                    FROM users WHERE id = %s
                """, (user_id,))
                result = cursor.fetchone()
                
                return {
                    "id": result['id'],
                    "username": result['username'],
                    "email": result['email'],
                    "role": result['role'],
                    "theme": result['theme'],
                    "is_active": bool(result['is_active']),
                    "created_at": str(result['created_at']) if result['created_at'] else None,
                    "updated_at": str(result['updated_at']) if result['updated_at'] else None
                }
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")
        finally:
            connection.close()
    
    @app.delete("/api/users/{user_id}")
    async def delete_user_api(user_id: int):
        """删除用户"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查用户是否存在
                cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                # 防止删除管理员账号
                if user['username'] == 'admin':
                    raise HTTPException(status_code=400, detail="不能删除管理员账号")
                
                # 检查是否是已经标记为删除的用户
                is_already_deleted = '_del_' in user['username'] or '_deleted_' in user['username']
                
                # 检查是否有相关的审计日志记录
                cursor.execute("SELECT COUNT(*) as count FROM audit_logs WHERE user_id = %s", (user_id,))
                audit_count = cursor.fetchone()['count']
                
                if audit_count > 0 and not is_already_deleted:
                    # 如果有审计日志且未被标记删除，将用户标记为删除而不是物理删除
                    # 使用更短的删除标记格式，避免超过字段长度限制
                    import time
                    short_timestamp = str(int(time.time()))[-6:]  # 只取时间戳的后6位
                    
                    # 确保新用户名不超过50个字符
                    original_username = user['username']
                    max_prefix_length = 50 - len('_del_') - len(short_timestamp)
                    if len(original_username) > max_prefix_length:
                        username_prefix = original_username[:max_prefix_length]
                    else:
                        username_prefix = original_username
                    
                    new_username = f"{username_prefix}_del_{short_timestamp}"
                    
                    cursor.execute("""
                        UPDATE users SET 
                            is_active = FALSE, 
                            username = %s,
                            email = CASE 
                                WHEN email IS NOT NULL THEN CONCAT(LEFT(email, 80), '_del_', %s) 
                                ELSE NULL 
                            END,
                            updated_at = NOW() 
                        WHERE id = %s
                    """, (new_username, short_timestamp, user_id))
                    message = "用户已标记为删除（保留审计记录）"
                elif is_already_deleted:
                    # 如果用户已经被标记为删除，执行强制删除
                    # 先删除审计日志记录
                    cursor.execute("DELETE FROM audit_logs WHERE user_id = %s", (user_id,))
                    
                    # 删除可能的相关记录
                    cursor.execute("DELETE FROM ip_addresses WHERE allocated_by = %s", (user_id,))
                    cursor.execute("DELETE FROM subnets WHERE created_by = %s", (user_id,))
                    
                    # 删除用户
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    message = "用户强制删除成功（已清理所有相关记录）"
                else:
                    # 如果没有审计日志，可以安全删除
                    # 先删除可能的相关记录
                    cursor.execute("DELETE FROM ip_addresses WHERE allocated_by = %s", (user_id,))
                    cursor.execute("DELETE FROM subnets WHERE created_by = %s", (user_id,))
                    
                    # 删除用户
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    message = "用户删除成功"
                
                connection.commit()
                
                return {"message": message}
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")
        finally:
            connection.close()
    
    @app.put("/api/users/{user_id}/password")
    async def reset_user_password_api(user_id: int, data: dict):
        """重置用户密码"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                new_password = data.get('new_password')
                
                if not new_password:
                    raise HTTPException(status_code=400, detail="新密码不能为空")
                
                if len(new_password) < 8:
                    raise HTTPException(status_code=400, detail="密码长度至少8位")
                
                # 检查用户是否存在
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                # 更新密码（简单的密码哈希，生产环境应使用bcrypt）
                import hashlib
                password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                
                cursor.execute("""
                    UPDATE users SET password_hash = %s, updated_at = NOW() 
                    WHERE id = %s
                """, (password_hash, user_id))
                
                connection.commit()
                
                return {"message": "密码重置成功"}
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"重置密码失败: {str(e)}")
        finally:
            connection.close()
    
    @app.put("/api/users/{user_id}/toggle-status")
    async def toggle_user_status_api(user_id: int):
        """切换用户激活状态"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查用户是否存在
                cursor.execute("SELECT id, username, is_active FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                # 防止停用管理员账号
                if user['username'] == 'admin':
                    raise HTTPException(status_code=400, detail="不能停用管理员账号")
                
                # 切换状态
                new_status = not bool(user['is_active'])
                cursor.execute("""
                    UPDATE users SET is_active = %s, updated_at = NOW() 
                    WHERE id = %s
                """, (new_status, user_id))
                
                connection.commit()
                
                action = "激活" if new_status else "停用"
                return {
                    "id": user_id,
                    "is_active": new_status,
                    "message": f"用户已{action}"
                }
        except HTTPException:
            raise
        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"切换用户状态失败: {str(e)}")
        finally:
            connection.close()

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