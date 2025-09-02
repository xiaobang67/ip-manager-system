"""
API集成测试
测试所有API接口的集成功能
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.database import get_db
from app.models import User, Subnet, IPAddress, AuditLog
from app.auth import create_access_token
from app.core.security import get_password_hash
import json


class TestAuthAPI:
    """认证API测试"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """测试成功登录"""
        response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """测试无效凭据登录"""
        response = await client.post("/api/auth/login", json={
            "username": "invalid",
            "password": "invalid"
        })
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient, auth_headers):
        """测试获取用户信息"""
        response = await client.get("/api/auth/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
        assert "email" in data

    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, auth_headers):
        """测试更新用户信息"""
        response = await client.put("/api/auth/profile", 
            headers=auth_headers,
            json={
                "email": "newemail@test.com",
                "theme": "dark"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@test.com"
        assert data["theme"] == "dark"

    @pytest.mark.asyncio
    async def test_change_password(self, client: AsyncClient, auth_headers):
        """测试修改密码"""
        response = await client.put("/api/auth/password",
            headers=auth_headers,
            json={
                "old_password": "testpass123",
                "new_password": "newpass123"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"

    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, client: AsyncClient, auth_headers):
        """测试错误的旧密码"""
        response = await client.put("/api/auth/password",
            headers=auth_headers,
            json={
                "old_password": "wrongpass",
                "new_password": "newpass123"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid old password" in response.json()["detail"]


class TestSubnetAPI:
    """网段API测试"""
    
    @pytest.mark.asyncio
    async def test_create_subnet(self, client: AsyncClient, auth_headers):
        """测试创建网段"""
        subnet_data = {
            "network": "192.168.100.0/24",
            "netmask": "255.255.255.0",
            "gateway": "192.168.100.1",
            "description": "Test Network",
            "vlan_id": 100,
            "location": "Test Location"
        }
        
        response = await client.post("/api/subnets", 
            headers=auth_headers,
            json=subnet_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["network"] == subnet_data["network"]
        assert data["gateway"] == subnet_data["gateway"]
        assert data["description"] == subnet_data["description"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_subnets(self, client: AsyncClient, auth_headers, test_subnet):
        """测试获取网段列表"""
        response = await client.get("/api/subnets", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
        assert data["items"][0]["network"] == "192.168.1.0/24"

    @pytest.mark.asyncio
    async def test_get_subnet_by_id(self, client: AsyncClient, auth_headers, test_subnet):
        """测试根据ID获取网段"""
        response = await client.get(f"/api/subnets/{test_subnet.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_subnet.id
        assert data["network"] == test_subnet.network

    @pytest.mark.asyncio
    async def test_update_subnet(self, client: AsyncClient, auth_headers, test_subnet):
        """测试更新网段"""
        update_data = {
            "description": "Updated Test Network",
            "location": "Updated Location"
        }
        
        response = await client.put(f"/api/subnets/{test_subnet.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["location"] == update_data["location"]

    @pytest.mark.asyncio
    async def test_delete_subnet_with_allocated_ips(self, client: AsyncClient, auth_headers, test_subnet_with_ips):
        """测试删除有已分配IP的网段"""
        response = await client.delete(f"/api/subnets/{test_subnet_with_ips.id}", headers=auth_headers)
        
        assert response.status_code == 400
        assert "allocated IP addresses" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_empty_subnet(self, client: AsyncClient, auth_headers, test_subnet):
        """测试删除空网段"""
        response = await client.delete(f"/api/subnets/{test_subnet.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Subnet deleted successfully"

    @pytest.mark.asyncio
    async def test_validate_subnet_format(self, client: AsyncClient, auth_headers):
        """测试网段格式验证"""
        # 有效网段
        response = await client.post("/api/subnets/validate",
            headers=auth_headers,
            json={"network": "10.0.0.0/16"}
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True
        
        # 无效网段
        response = await client.post("/api/subnets/validate",
            headers=auth_headers,
            json={"network": "invalid-network"}
        )
        assert response.status_code == 200
        assert response.json()["valid"] is False

    @pytest.mark.asyncio
    async def test_subnet_overlap_detection(self, client: AsyncClient, auth_headers, test_subnet):
        """测试网段重叠检测"""
        overlapping_subnet = {
            "network": "192.168.1.0/25",  # 与现有网段重叠
            "netmask": "255.255.255.128",
            "gateway": "192.168.1.1"
        }
        
        response = await client.post("/api/subnets",
            headers=auth_headers,
            json=overlapping_subnet
        )
        
        assert response.status_code == 400
        assert "overlap" in response.json()["detail"].lower()


class TestIPAPI:
    """IP地址API测试"""
    
    @pytest.mark.asyncio
    async def test_get_ips(self, client: AsyncClient, auth_headers, test_subnet_with_ips):
        """测试获取IP地址列表"""
        response = await client.get("/api/ips", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_allocate_ip(self, client: AsyncClient, auth_headers, test_subnet_with_ips):
        """测试分配IP地址"""
        allocation_data = {
            "mac_address": "00:11:22:33:44:55",
            "hostname": "test-server",
            "device_type": "Server",
            "assigned_to": "IT Department",
            "description": "Test allocation"
        }
        
        # 找到一个可用的IP地址
        response = await client.get("/api/ips?status=available", headers=auth_headers)
        available_ips = response.json()["items"]
        assert len(available_ips) > 0
        
        ip_address = available_ips[0]["ip_address"]
        
        response = await client.post(f"/api/ips/allocate",
            headers=auth_headers,
            json={
                "ip_address": ip_address,
                **allocation_data
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "allocated"
        assert data["mac_address"] == allocation_data["mac_address"]
        assert data["hostname"] == allocation_data["hostname"]

    @pytest.mark.asyncio
    async def test_reserve_ip(self, client: AsyncClient, auth_headers, test_subnet_with_ips):
        """测试保留IP地址"""
        # 找到一个可用的IP地址
        response = await client.get("/api/ips?status=available", headers=auth_headers)
        available_ips = response.json()["items"]
        ip_address = available_ips[0]["ip_address"]
        
        response = await client.put(f"/api/ips/{ip_address}/reserve",
            headers=auth_headers,
            json={"reason": "Reserved for future use"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reserved"
        assert "Reserved for future use" in data["description"]

    @pytest.mark.asyncio
    async def test_release_ip(self, client: AsyncClient, auth_headers, test_allocated_ip):
        """测试释放IP地址"""
        response = await client.put(f"/api/ips/{test_allocated_ip.ip_address}/release",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "available"
        assert data["mac_address"] is None
        assert data["hostname"] is None

    @pytest.mark.asyncio
    async def test_search_ips(self, client: AsyncClient, auth_headers, test_allocated_ip):
        """测试搜索IP地址"""
        # 按IP地址搜索
        response = await client.get(f"/api/ips/search?query={test_allocated_ip.ip_address}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(ip["ip_address"] == test_allocated_ip.ip_address for ip in data["items"])
        
        # 按主机名搜索
        if test_allocated_ip.hostname:
            response = await client.get(f"/api/ips/search?query={test_allocated_ip.hostname}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_ip_history(self, client: AsyncClient, auth_headers, test_allocated_ip):
        """测试获取IP历史记录"""
        response = await client.get(f"/api/ips/{test_allocated_ip.ip_address}/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 应该至少有一条分配记录
        assert len(data) >= 1
        assert any(record["action"] == "allocate" for record in data)

    @pytest.mark.asyncio
    async def test_conflict_check(self, client: AsyncClient, auth_headers):
        """测试冲突检测"""
        response = await client.post("/api/ips/conflict-check", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "conflicts" in data
        assert isinstance(data["conflicts"], list)

    @pytest.mark.asyncio
    async def test_allocate_already_allocated_ip(self, client: AsyncClient, auth_headers, test_allocated_ip):
        """测试分配已分配的IP地址"""
        allocation_data = {
            "ip_address": test_allocated_ip.ip_address,
            "mac_address": "00:11:22:33:44:66",
            "hostname": "another-server"
        }
        
        response = await client.post("/api/ips/allocate",
            headers=auth_headers,
            json=allocation_data
        )
        
        assert response.status_code == 400
        assert "already allocated" in response.json()["detail"].lower()


class TestUserAPI:
    """用户API测试"""
    
    @pytest.mark.asyncio
    async def test_get_users(self, client: AsyncClient, admin_headers):
        """测试获取用户列表"""
        response = await client.get("/api/users", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient, admin_headers):
        """测试创建用户"""
        user_data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "newpass123",
            "role": "user",
            "theme": "light"
        }
        
        response = await client.post("/api/users",
            headers=admin_headers,
            json=user_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]
        assert "password" not in data  # 密码不应该返回

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, admin_headers, test_user):
        """测试更新用户"""
        update_data = {
            "email": "updated@test.com",
            "theme": "dark"
        }
        
        response = await client.put(f"/api/users/{test_user.id}",
            headers=admin_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == update_data["email"]
        assert data["theme"] == update_data["theme"]

    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, admin_headers):
        """测试删除用户"""
        # 先创建一个用户用于删除
        user_data = {
            "username": "todelete",
            "email": "todelete@test.com",
            "password": "pass123",
            "role": "user"
        }
        
        create_response = await client.post("/api/users",
            headers=admin_headers,
            json=user_data
        )
        user_id = create_response.json()["id"]
        
        # 删除用户
        response = await client.delete(f"/api/users/{user_id}", headers=admin_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"

    @pytest.mark.asyncio
    async def test_update_user_role(self, client: AsyncClient, admin_headers, test_user):
        """测试更新用户角色"""
        response = await client.put(f"/api/users/{test_user.id}/role",
            headers=admin_headers,
            json={"role": "manager"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "manager"

    @pytest.mark.asyncio
    async def test_get_user_permissions(self, client: AsyncClient, auth_headers, test_user):
        """测试获取用户权限"""
        response = await client.get(f"/api/users/{test_user.id}/permissions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)

    @pytest.mark.asyncio
    async def test_create_duplicate_username(self, client: AsyncClient, admin_headers, test_user):
        """测试创建重复用户名"""
        user_data = {
            "username": test_user.username,  # 重复的用户名
            "email": "different@test.com",
            "password": "pass123",
            "role": "user"
        }
        
        response = await client.post("/api/users",
            headers=admin_headers,
            json=user_data
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()


class TestReportAPI:
    """报告API测试"""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, client: AsyncClient, auth_headers, test_subnet_with_ips):
        """测试获取仪表盘数据"""
        response = await client.get("/api/reports/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_subnets" in data
        assert "total_ips" in data
        assert "allocated_ips" in data
        assert "available_ips" in data
        assert "utilization_rate" in data

    @pytest.mark.asyncio
    async def test_get_utilization_report(self, client: AsyncClient, auth_headers, test_subnet_with_ips):
        """测试获取使用率报告"""
        response = await client.get("/api/reports/utilization", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "subnets" in data
        assert isinstance(data["subnets"], list)
        if len(data["subnets"]) > 0:
            subnet = data["subnets"][0]
            assert "network" in subnet
            assert "utilization_rate" in subnet
            assert "total_ips" in subnet
            assert "allocated_ips" in subnet

    @pytest.mark.asyncio
    async def test_get_inventory_report(self, client: AsyncClient, auth_headers, test_allocated_ip):
        """测试获取清单报告"""
        response = await client.get("/api/reports/inventory", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "ips" in data
        assert isinstance(data["ips"], list)

    @pytest.mark.asyncio
    async def test_export_report(self, client: AsyncClient, auth_headers):
        """测试导出报告"""
        export_data = {
            "report_type": "utilization",
            "format": "csv"
        }
        
        response = await client.post("/api/reports/export",
            headers=auth_headers,
            json=export_data
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"

    @pytest.mark.asyncio
    async def test_get_alerts(self, client: AsyncClient, auth_headers):
        """测试获取警报"""
        response = await client.get("/api/reports/alerts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)


class TestPermissions:
    """权限测试"""
    
    @pytest.mark.asyncio
    async def test_user_cannot_access_admin_endpoints(self, client: AsyncClient, user_headers):
        """测试普通用户无法访问管理员接口"""
        # 尝试创建用户
        response = await client.post("/api/users",
            headers=user_headers,
            json={
                "username": "test",
                "email": "test@test.com",
                "password": "pass123"
            }
        )
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_user_can_read_own_data(self, client: AsyncClient, user_headers):
        """测试用户可以读取自己的数据"""
        response = await client.get("/api/auth/profile", headers=user_headers)
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_manager_can_manage_ips(self, client: AsyncClient, manager_headers, test_subnet_with_ips):
        """测试管理员可以管理IP地址"""
        # 获取可用IP
        response = await client.get("/api/ips?status=available", headers=manager_headers)
        available_ips = response.json()["items"]
        
        if len(available_ips) > 0:
            ip_address = available_ips[0]["ip_address"]
            
            # 分配IP
            response = await client.post("/api/ips/allocate",
                headers=manager_headers,
                json={
                    "ip_address": ip_address,
                    "hostname": "manager-test"
                }
            )
            
            assert response.status_code == 200


class TestAuditLog:
    """审计日志测试"""
    
    @pytest.mark.asyncio
    async def test_operations_are_logged(self, client: AsyncClient, auth_headers, db_session):
        """测试操作被记录到审计日志"""
        # 执行一个操作（创建网段）
        subnet_data = {
            "network": "10.10.0.0/24",
            "netmask": "255.255.255.0",
            "gateway": "10.10.0.1",
            "description": "Audit test network"
        }
        
        response = await client.post("/api/subnets",
            headers=auth_headers,
            json=subnet_data
        )
        
        assert response.status_code == 201
        
        # 检查审计日志
        audit_logs = await db_session.execute(
            "SELECT * FROM audit_logs WHERE action = 'CREATE' AND entity_type = 'subnet'"
        )
        logs = audit_logs.fetchall()
        
        assert len(logs) >= 1
        log = logs[-1]  # 最新的日志
        assert log.action == "CREATE"
        assert log.entity_type == "subnet"
        assert log.new_values is not None


class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_invalid_json_request(self, client: AsyncClient, auth_headers):
        """测试无效JSON请求"""
        response = await client.post("/api/subnets",
            headers=auth_headers,
            content="invalid json"
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient, auth_headers):
        """测试缺少必需字段"""
        response = await client.post("/api/subnets",
            headers=auth_headers,
            json={"description": "Missing network field"}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_ip_format(self, client: AsyncClient, auth_headers):
        """测试无效IP格式"""
        response = await client.post("/api/subnets",
            headers=auth_headers,
            json={
                "network": "invalid-ip-format",
                "netmask": "255.255.255.0"
            }
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """测试未授权访问"""
        response = await client.get("/api/subnets")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_not_found_resource(self, client: AsyncClient, auth_headers):
        """测试资源不存在"""
        response = await client.get("/api/subnets/99999", headers=auth_headers)
        
        assert response.status_code == 404


class TestDataValidation:
    """数据验证测试"""
    
    @pytest.mark.asyncio
    async def test_ip_address_validation(self, client: AsyncClient, auth_headers):
        """测试IP地址格式验证"""
        invalid_ips = [
            "256.1.1.1",
            "192.168.1",
            "192.168.1.1.1",
            "not-an-ip"
        ]
        
        for invalid_ip in invalid_ips:
            response = await client.post("/api/ips/allocate",
                headers=auth_headers,
                json={
                    "ip_address": invalid_ip,
                    "hostname": "test"
                }
            )
            
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_mac_address_validation(self, client: AsyncClient, auth_headers, test_subnet_with_ips):
        """测试MAC地址格式验证"""
        # 获取可用IP
        response = await client.get("/api/ips?status=available", headers=auth_headers)
        available_ips = response.json()["items"]
        ip_address = available_ips[0]["ip_address"]
        
        invalid_macs = [
            "invalid-mac",
            "00:11:22:33:44",  # 太短
            "00:11:22:33:44:55:66",  # 太长
            "GG:11:22:33:44:55"  # 无效字符
        ]
        
        for invalid_mac in invalid_macs:
            response = await client.post("/api/ips/allocate",
                headers=auth_headers,
                json={
                    "ip_address": ip_address,
                    "mac_address": invalid_mac,
                    "hostname": "test"
                }
            )
            
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_email_validation(self, client: AsyncClient, admin_headers):
        """测试邮箱格式验证"""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user@domain"
        ]
        
        for invalid_email in invalid_emails:
            response = await client.post("/api/users",
                headers=admin_headers,
                json={
                    "username": f"user_{invalid_email.replace('@', '_').replace('.', '_')}",
                    "email": invalid_email,
                    "password": "pass123"
                }
            )
            
            assert response.status_code == 422