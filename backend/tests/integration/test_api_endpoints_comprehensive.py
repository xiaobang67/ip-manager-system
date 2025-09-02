"""
API端点集成测试 - 全面覆盖
"""
import pytest
import json
from fastapi.testclient import TestClient

from tests.factories import (
    UserFactory, SubnetFactory, IPAddressFactory, 
    AllocatedIPFactory, TagFactory
)


class TestAuthenticationAPI:
    """认证API集成测试"""

    @pytest.mark.integration
    def test_login_success(self, client, test_user):
        """测试成功登录"""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.integration
    def test_login_invalid_credentials(self, client, test_user):
        """测试无效凭据登录"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.integration
    def test_protected_endpoint_without_token(self, client):
        """测试无token访问受保护端点"""
        response = client.get("/api/users/profile")
        
        assert response.status_code == 401

    @pytest.mark.integration
    def test_protected_endpoint_with_token(self, client, auth_headers):
        """测试有效token访问受保护端点"""
        response = client.get("/api/users/profile", headers=auth_headers)
        
        assert response.status_code == 200

    @pytest.mark.integration
    def test_token_refresh(self, client, auth_headers):
        """测试token刷新"""
        response = client.post("/api/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.integration
    def test_logout(self, client, auth_headers):
        """测试登出"""
        response = client.post("/api/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200


class TestSubnetAPI:
    """网段API集成测试"""

    @pytest.mark.integration
    def test_create_subnet_success(self, client, admin_headers, db_session):
        """测试成功创建网段"""
        subnet_data = {
            "network": "192.168.100.0/24",
            "netmask": "255.255.255.0",
            "gateway": "192.168.100.1",
            "description": "Test subnet",
            "vlan_id": 100,
            "location": "Office"
        }
        
        response = client.post("/api/subnets", json=subnet_data, headers=admin_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["network"] == "192.168.100.0/24"
        assert data["description"] == "Test subnet"

    @pytest.mark.integration
    def test_create_subnet_invalid_format(self, client, admin_headers):
        """测试创建无效格式网段"""
        subnet_data = {
            "network": "invalid_network",
            "netmask": "255.255.255.0"
        }
        
        response = client.post("/api/subnets", json=subnet_data, headers=admin_headers)
        
        assert response.status_code == 422

    @pytest.mark.integration
    def test_get_subnets_list(self, client, auth_headers, db_session):
        """测试获取网段列表"""
        # 创建测试数据
        subnet1 = SubnetFactory(network="192.168.1.0/24")
        subnet2 = SubnetFactory(network="192.168.2.0/24")
        db_session.add_all([subnet1, subnet2])
        db_session.commit()
        
        response = client.get("/api/subnets", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 2

    @pytest.mark.integration
    def test_get_subnet_by_id(self, client, auth_headers, db_session):
        """测试根据ID获取网段"""
        subnet = SubnetFactory(network="192.168.3.0/24")
        db_session.add(subnet)
        db_session.commit()
        
        response = client.get(f"/api/subnets/{subnet.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["network"] == "192.168.3.0/24"

    @pytest.mark.integration
    def test_update_subnet(self, client, admin_headers, db_session):
        """测试更新网段"""
        subnet = SubnetFactory(network="192.168.4.0/24")
        db_session.add(subnet)
        db_session.commit()
        
        update_data = {
            "description": "Updated description",
            "vlan_id": 200
        }
        
        response = client.put(f"/api/subnets/{subnet.id}", json=update_data, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["vlan_id"] == 200

    @pytest.mark.integration
    def test_delete_empty_subnet(self, client, admin_headers, db_session):
        """测试删除空网段"""
        subnet = SubnetFactory(network="192.168.5.0/24")
        db_session.add(subnet)
        db_session.commit()
        
        response = client.delete(f"/api/subnets/{subnet.id}", headers=admin_headers)
        
        assert response.status_code == 204

    @pytest.mark.integration
    def test_delete_subnet_with_allocated_ips(self, client, admin_headers, db_session):
        """测试删除包含已分配IP的网段"""
        subnet = SubnetFactory(network="192.168.6.0/24")
        allocated_ip = AllocatedIPFactory(subnet=subnet, ip_address="192.168.6.10")
        db_session.add_all([subnet, allocated_ip])
        db_session.commit()
        
        response = client.delete(f"/api/subnets/{subnet.id}", headers=admin_headers)
        
        assert response.status_code == 400
        assert "cannot be deleted" in response.json()["detail"].lower()


class TestIPAddressAPI:
    """IP地址API集成测试"""

    @pytest.mark.integration
    def test_get_ip_addresses_list(self, client, auth_headers, db_session):
        """测试获取IP地址列表"""
        subnet = SubnetFactory(network="192.168.10.0/24")
        ip1 = IPAddressFactory(subnet=subnet, ip_address="192.168.10.10")
        ip2 = IPAddressFactory(subnet=subnet, ip_address="192.168.10.11")
        db_session.add_all([subnet, ip1, ip2])
        db_session.commit()
        
        response = client.get("/api/ips", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 2

    @pytest.mark.integration
    def test_allocate_ip_address(self, client, admin_headers, db_session):
        """测试分配IP地址"""
        subnet = SubnetFactory(network="192.168.11.0/24")
        available_ip = IPAddressFactory(
            subnet=subnet, 
            ip_address="192.168.11.10",
            status="available"
        )
        db_session.add_all([subnet, available_ip])
        db_session.commit()
        
        allocation_data = {
            "hostname": "test-server",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "device_type": "Server",
            "assigned_to": "John Doe"
        }
        
        response = client.post(
            f"/api/ips/{available_ip.ip_address}/allocate",
            json=allocation_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "allocated"
        assert data["hostname"] == "test-server"

    @pytest.mark.integration
    def test_allocate_already_allocated_ip(self, client, admin_headers, db_session):
        """测试分配已分配的IP地址"""
        subnet = SubnetFactory(network="192.168.12.0/24")
        allocated_ip = AllocatedIPFactory(
            subnet=subnet,
            ip_address="192.168.12.10"
        )
        db_session.add_all([subnet, allocated_ip])
        db_session.commit()
        
        allocation_data = {
            "hostname": "test-server",
            "mac_address": "AA:BB:CC:DD:EE:FF"
        }
        
        response = client.post(
            f"/api/ips/{allocated_ip.ip_address}/allocate",
            json=allocation_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400

    @pytest.mark.integration
    def test_reserve_ip_address(self, client, admin_headers, db_session):
        """测试保留IP地址"""
        subnet = SubnetFactory(network="192.168.13.0/24")
        available_ip = IPAddressFactory(
            subnet=subnet,
            ip_address="192.168.13.10",
            status="available"
        )
        db_session.add_all([subnet, available_ip])
        db_session.commit()
        
        reservation_data = {
            "description": "Reserved for future server"
        }
        
        response = client.post(
            f"/api/ips/{available_ip.ip_address}/reserve",
            json=reservation_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reserved"

    @pytest.mark.integration
    def test_release_ip_address(self, client, admin_headers, db_session):
        """测试释放IP地址"""
        subnet = SubnetFactory(network="192.168.14.0/24")
        allocated_ip = AllocatedIPFactory(
            subnet=subnet,
            ip_address="192.168.14.10"
        )
        db_session.add_all([subnet, allocated_ip])
        db_session.commit()
        
        response = client.post(
            f"/api/ips/{allocated_ip.ip_address}/release",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "available"

    @pytest.mark.integration
    def test_search_ip_addresses(self, client, auth_headers, db_session):
        """测试搜索IP地址"""
        subnet = SubnetFactory(network="192.168.15.0/24")
        ip1 = IPAddressFactory(
            subnet=subnet,
            ip_address="192.168.15.10",
            hostname="web-server"
        )
        ip2 = IPAddressFactory(
            subnet=subnet,
            ip_address="192.168.15.11",
            hostname="db-server"
        )
        db_session.add_all([subnet, ip1, ip2])
        db_session.commit()
        
        # 按主机名搜索
        response = client.get("/api/ips/search?hostname=web", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("web" in item["hostname"] for item in data["items"])

    @pytest.mark.integration
    def test_get_ip_history(self, client, auth_headers, db_session):
        """测试获取IP地址历史"""
        subnet = SubnetFactory(network="192.168.16.0/24")
        ip_address = AllocatedIPFactory(
            subnet=subnet,
            ip_address="192.168.16.10"
        )
        db_session.add_all([subnet, ip_address])
        db_session.commit()
        
        response = client.get(f"/api/ips/{ip_address.ip_address}/history", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_bulk_allocate_ips(self, client, admin_headers, db_session):
        """测试批量分配IP地址"""
        subnet = SubnetFactory(network="192.168.17.0/24")
        ip1 = IPAddressFactory(subnet=subnet, ip_address="192.168.17.10", status="available")
        ip2 = IPAddressFactory(subnet=subnet, ip_address="192.168.17.11", status="available")
        db_session.add_all([subnet, ip1, ip2])
        db_session.commit()
        
        bulk_data = {
            "ip_addresses": ["192.168.17.10", "192.168.17.11"],
            "hostname_prefix": "server",
            "device_type": "Server",
            "assigned_to": "IT Team"
        }
        
        response = client.post("/api/ips/bulk-allocate", json=bulk_data, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["allocated"]) == 2


class TestUserManagementAPI:
    """用户管理API集成测试"""

    @pytest.mark.integration
    def test_get_users_list(self, client, admin_headers, db_session):
        """测试获取用户列表"""
        response = client.get("/api/users", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.integration
    def test_create_user(self, client, admin_headers):
        """测试创建用户"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "role": "user"
        }
        
        response = client.post("/api/users", json=user_data, headers=admin_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"

    @pytest.mark.integration
    def test_update_user_profile(self, client, auth_headers, test_user):
        """测试更新用户资料"""
        update_data = {
            "email": "updated@example.com",
            "theme": "dark"
        }
        
        response = client.put("/api/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["theme"] == "dark"

    @pytest.mark.integration
    def test_change_password(self, client, auth_headers):
        """测试修改密码"""
        password_data = {
            "current_password": "testpass123",
            "new_password": "newpass456"
        }
        
        response = client.put("/api/users/password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200


class TestMonitoringAPI:
    """监控API集成测试"""

    @pytest.mark.integration
    def test_get_dashboard_stats(self, client, auth_headers, db_session):
        """测试获取仪表盘统计"""
        # 创建测试数据
        subnet = SubnetFactory(network="192.168.20.0/24")
        ip1 = AllocatedIPFactory(subnet=subnet, ip_address="192.168.20.10")
        ip2 = IPAddressFactory(subnet=subnet, ip_address="192.168.20.11", status="available")
        db_session.add_all([subnet, ip1, ip2])
        db_session.commit()
        
        response = client.get("/api/monitoring/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_subnets" in data
        assert "total_ips" in data
        assert "allocated_ips" in data
        assert "utilization_rate" in data

    @pytest.mark.integration
    def test_get_subnet_utilization(self, client, auth_headers, db_session):
        """测试获取网段使用率"""
        subnet = SubnetFactory(network="192.168.21.0/24")
        db_session.add(subnet)
        db_session.commit()
        
        response = client.get(f"/api/monitoring/subnets/{subnet.id}/utilization", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_ips" in data
        assert "allocated_ips" in data
        assert "utilization_percentage" in data

    @pytest.mark.integration
    def test_generate_report(self, client, admin_headers, db_session):
        """测试生成报告"""
        report_data = {
            "report_type": "utilization",
            "format": "json",
            "date_range": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        }
        
        response = client.post("/api/reports/generate", json=report_data, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data or "data" in data


class TestTagsAPI:
    """标签API集成测试"""

    @pytest.mark.integration
    def test_create_tag(self, client, admin_headers):
        """测试创建标签"""
        tag_data = {
            "name": "production",
            "color": "#ff0000",
            "description": "Production environment"
        }
        
        response = client.post("/api/tags", json=tag_data, headers=admin_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "production"
        assert data["color"] == "#ff0000"

    @pytest.mark.integration
    def test_assign_tag_to_ip(self, client, admin_headers, db_session):
        """测试为IP地址分配标签"""
        subnet = SubnetFactory(network="192.168.22.0/24")
        ip_address = IPAddressFactory(subnet=subnet, ip_address="192.168.22.10")
        tag = TagFactory(name="server")
        db_session.add_all([subnet, ip_address, tag])
        db_session.commit()
        
        response = client.post(
            f"/api/ips/{ip_address.ip_address}/tags/{tag.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200

    @pytest.mark.integration
    def test_get_tags_list(self, client, auth_headers, db_session):
        """测试获取标签列表"""
        tag1 = TagFactory(name="web")
        tag2 = TagFactory(name="database")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        
        response = client.get("/api/tags", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2


class TestErrorHandling:
    """错误处理集成测试"""

    @pytest.mark.integration
    def test_404_not_found(self, client, auth_headers):
        """测试404错误"""
        response = client.get("/api/nonexistent", headers=auth_headers)
        
        assert response.status_code == 404

    @pytest.mark.integration
    def test_validation_error(self, client, admin_headers):
        """测试验证错误"""
        invalid_data = {
            "network": "",  # 空网段
            "netmask": "invalid"
        }
        
        response = client.post("/api/subnets", json=invalid_data, headers=admin_headers)
        
        assert response.status_code == 422

    @pytest.mark.integration
    def test_permission_denied(self, client, auth_headers):
        """测试权限拒绝"""
        # 普通用户尝试创建用户
        user_data = {
            "username": "unauthorized",
            "password": "pass123"
        }
        
        response = client.post("/api/users", json=user_data, headers=auth_headers)
        
        assert response.status_code == 403