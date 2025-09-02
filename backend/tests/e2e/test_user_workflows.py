"""
端到端测试 - 用户工作流程
"""
import pytest
from fastapi.testclient import TestClient

from tests.factories import UserFactory, SubnetFactory


class TestCompleteUserWorkflows:
    """完整用户工作流程测试"""

    @pytest.mark.e2e
    def test_complete_ip_management_workflow(self, client, db_session):
        """测试完整的IP管理工作流程"""
        # 1. 创建管理员用户
        admin = UserFactory(username="workflow_admin", role="admin")
        db_session.add(admin)
        db_session.commit()
        
        # 2. 管理员登录
        login_response = client.post("/api/auth/login", json={
            "username": "workflow_admin",
            "password": "testpass123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. 创建网段
        subnet_data = {
            "network": "10.1.0.0/24",
            "netmask": "255.255.255.0",
            "gateway": "10.1.0.1",
            "description": "E2E Test Subnet",
            "vlan_id": 100
        }
        subnet_response = client.post("/api/subnets", json=subnet_data, headers=headers)
        assert subnet_response.status_code == 201
        subnet_id = subnet_response.json()["id"]
        
        # 4. 验证IP地址自动生成
        ips_response = client.get(f"/api/subnets/{subnet_id}/ips", headers=headers)
        assert ips_response.status_code == 200
        ips = ips_response.json()["items"]
        assert len(ips) > 0
        
        # 5. 分配第一个可用IP
        available_ip = next(ip for ip in ips if ip["status"] == "available")
        allocation_data = {
            "hostname": "e2e-test-server",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "device_type": "Server",
            "assigned_to": "E2E Test"
        }
        allocate_response = client.post(
            f"/api/ips/{available_ip['ip_address']}/allocate",
            json=allocation_data,
            headers=headers
        )
        assert allocate_response.status_code == 200
        allocated_ip = allocate_response.json()
        assert allocated_ip["status"] == "allocated"
        assert allocated_ip["hostname"] == "e2e-test-server"
        
        # 6. 搜索已分配的IP
        search_response = client.get(
            f"/api/ips/search?hostname=e2e-test-server",
            headers=headers
        )
        assert search_response.status_code == 200
        search_results = search_response.json()["items"]
        assert len(search_results) == 1
        assert search_results[0]["hostname"] == "e2e-test-server"
        
        # 7. 查看IP历史记录
        history_response = client.get(
            f"/api/ips/{available_ip['ip_address']}/history",
            headers=headers
        )
        assert history_response.status_code == 200
        
        # 8. 释放IP地址
        release_response = client.post(
            f"/api/ips/{available_ip['ip_address']}/release",
            headers=headers
        )
        assert release_response.status_code == 200
        released_ip = release_response.json()
        assert released_ip["status"] == "available"
        
        # 9. 删除网段
        delete_response = client.delete(f"/api/subnets/{subnet_id}", headers=headers)
        assert delete_response.status_code == 204

    @pytest.mark.e2e
    def test_user_management_workflow(self, client, db_session):
        """测试用户管理工作流程"""
        # 1. 创建超级管理员
        super_admin = UserFactory(username="super_admin", role="admin")
        db_session.add(super_admin)
        db_session.commit()
        
        # 2. 超级管理员登录
        login_response = client.post("/api/auth/login", json={
            "username": "super_admin",
            "password": "testpass123"
        })
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 3. 创建新用户
        new_user_data = {
            "username": "new_employee",
            "email": "employee@company.com",
            "password": "employee123",
            "role": "user"
        }
        create_user_response = client.post("/api/users", json=new_user_data, headers=admin_headers)
        assert create_user_response.status_code == 201
        new_user = create_user_response.json()
        
        # 4. 新用户登录
        user_login_response = client.post("/api/auth/login", json={
            "username": "new_employee",
            "password": "employee123"
        })
        assert user_login_response.status_code == 200
        user_token = user_login_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # 5. 新用户查看个人资料
        profile_response = client.get("/api/users/profile", headers=user_headers)
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["username"] == "new_employee"
        
        # 6. 新用户更新个人资料
        update_data = {
            "email": "updated_employee@company.com",
            "theme": "dark"
        }
        update_response = client.put("/api/users/profile", json=update_data, headers=user_headers)
        assert update_response.status_code == 200
        updated_profile = update_response.json()
        assert updated_profile["email"] == "updated_employee@company.com"
        assert updated_profile["theme"] == "dark"
        
        # 7. 新用户修改密码
        password_data = {
            "current_password": "employee123",
            "new_password": "newpassword456"
        }
        password_response = client.put("/api/users/password", json=password_data, headers=user_headers)
        assert password_response.status_code == 200
        
        # 8. 使用新密码登录
        new_login_response = client.post("/api/auth/login", json={
            "username": "new_employee",
            "password": "newpassword456"
        })
        assert new_login_response.status_code == 200
        
        # 9. 管理员更新用户角色
        role_update_data = {"role": "manager"}
        role_response = client.put(
            f"/api/users/{new_user['id']}/role",
            json=role_update_data,
            headers=admin_headers
        )
        assert role_response.status_code == 200

    @pytest.mark.e2e
    def test_subnet_management_workflow(self, client, db_session):
        """测试网段管理工作流程"""
        # 1. 创建网络管理员
        network_admin = UserFactory(username="network_admin", role="admin")
        db_session.add(network_admin)
        db_session.commit()
        
        # 2. 登录
        login_response = client.post("/api/auth/login", json={
            "username": "network_admin",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. 创建多个网段
        subnets_data = [
            {
                "network": "172.16.1.0/24",
                "netmask": "255.255.255.0",
                "gateway": "172.16.1.1",
                "description": "Development Network",
                "vlan_id": 101
            },
            {
                "network": "172.16.2.0/24",
                "netmask": "255.255.255.0",
                "gateway": "172.16.2.1",
                "description": "Testing Network",
                "vlan_id": 102
            },
            {
                "network": "172.16.3.0/24",
                "netmask": "255.255.255.0",
                "gateway": "172.16.3.1",
                "description": "Production Network",
                "vlan_id": 103
            }
        ]
        
        created_subnets = []
        for subnet_data in subnets_data:
            response = client.post("/api/subnets", json=subnet_data, headers=headers)
            assert response.status_code == 201
            created_subnets.append(response.json())
        
        # 4. 获取网段列表并验证
        list_response = client.get("/api/subnets", headers=headers)
        assert list_response.status_code == 200
        subnets_list = list_response.json()["items"]
        assert len(subnets_list) >= 3
        
        # 5. 更新网段信息
        update_data = {
            "description": "Updated Development Network",
            "location": "Building A"
        }
        update_response = client.put(
            f"/api/subnets/{created_subnets[0]['id']}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        updated_subnet = update_response.json()
        assert updated_subnet["description"] == "Updated Development Network"
        
        # 6. 获取网段统计信息
        stats_response = client.get(
            f"/api/monitoring/subnets/{created_subnets[0]['id']}/utilization",
            headers=headers
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert "total_ips" in stats
        assert "utilization_percentage" in stats
        
        # 7. 分配一些IP地址
        ips_response = client.get(f"/api/subnets/{created_subnets[0]['id']}/ips", headers=headers)
        available_ips = [ip for ip in ips_response.json()["items"] if ip["status"] == "available"][:3]
        
        for i, ip in enumerate(available_ips):
            allocation_data = {
                "hostname": f"dev-server-{i+1}",
                "device_type": "Server",
                "assigned_to": "Development Team"
            }
            allocate_response = client.post(
                f"/api/ips/{ip['ip_address']}/allocate",
                json=allocation_data,
                headers=headers
            )
            assert allocate_response.status_code == 200
        
        # 8. 验证使用率更新
        updated_stats_response = client.get(
            f"/api/monitoring/subnets/{created_subnets[0]['id']}/utilization",
            headers=headers
        )
        updated_stats = updated_stats_response.json()
        assert updated_stats["allocated_ips"] >= 3
        
        # 9. 尝试删除有已分配IP的网段（应该失败）
        delete_response = client.delete(f"/api/subnets/{created_subnets[0]['id']}", headers=headers)
        assert delete_response.status_code == 400
        
        # 10. 删除空网段（应该成功）
        empty_delete_response = client.delete(f"/api/subnets/{created_subnets[2]['id']}", headers=headers)
        assert empty_delete_response.status_code == 204

    @pytest.mark.e2e
    def test_monitoring_and_reporting_workflow(self, client, db_session):
        """测试监控和报告工作流程"""
        # 1. 创建管理员
        admin = UserFactory(username="monitoring_admin", role="admin")
        db_session.add(admin)
        db_session.commit()
        
        # 2. 登录
        login_response = client.post("/api/auth/login", json={
            "username": "monitoring_admin",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. 创建测试环境
        subnet_data = {
            "network": "10.10.0.0/24",
            "netmask": "255.255.255.0",
            "gateway": "10.10.0.1",
            "description": "Monitoring Test Network"
        }
        subnet_response = client.post("/api/subnets", json=subnet_data, headers=headers)
        subnet_id = subnet_response.json()["id"]
        
        # 4. 分配一些IP地址以生成数据
        ips_response = client.get(f"/api/subnets/{subnet_id}/ips", headers=headers)
        available_ips = [ip for ip in ips_response.json()["items"] if ip["status"] == "available"][:10]
        
        for i, ip in enumerate(available_ips[:5]):  # 分配5个IP
            allocation_data = {
                "hostname": f"monitor-test-{i+1}",
                "device_type": "Server"
            }
            client.post(f"/api/ips/{ip['ip_address']}/allocate", json=allocation_data, headers=headers)
        
        for ip in available_ips[5:8]:  # 保留3个IP
            reservation_data = {"description": "Reserved for testing"}
            client.post(f"/api/ips/{ip['ip_address']}/reserve", json=reservation_data, headers=headers)
        
        # 5. 获取仪表盘统计
        dashboard_response = client.get("/api/monitoring/dashboard", headers=headers)
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        assert dashboard_data["total_subnets"] >= 1
        assert dashboard_data["allocated_ips"] >= 5
        
        # 6. 获取网段使用率
        utilization_response = client.get(
            f"/api/monitoring/subnets/{subnet_id}/utilization",
            headers=headers
        )
        assert utilization_response.status_code == 200
        utilization_data = utilization_response.json()
        assert utilization_data["allocated_ips"] == 5
        assert utilization_data["reserved_ips"] == 3
        
        # 7. 生成使用率报告
        report_data = {
            "report_type": "utilization",
            "format": "json",
            "subnet_ids": [subnet_id]
        }
        report_response = client.post("/api/reports/generate", json=report_data, headers=headers)
        assert report_response.status_code == 200
        
        # 8. 生成清单报告
        inventory_report_data = {
            "report_type": "inventory",
            "format": "json",
            "include_available": False  # 只包含已分配的IP
        }
        inventory_response = client.post("/api/reports/generate", json=inventory_report_data, headers=headers)
        assert inventory_response.status_code == 200

    @pytest.mark.e2e
    def test_search_and_filter_workflow(self, client, db_session):
        """测试搜索和过滤工作流程"""
        # 1. 创建用户并登录
        user = UserFactory(username="search_user", role="user")
        db_session.add(user)
        db_session.commit()
        
        login_response = client.post("/api/auth/login", json={
            "username": "search_user",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 创建测试数据
        subnet_data = {
            "network": "192.168.100.0/24",
            "netmask": "255.255.255.0",
            "gateway": "192.168.100.1",
            "description": "Search Test Network"
        }
        subnet_response = client.post("/api/subnets", json=subnet_data, headers=headers)
        subnet_id = subnet_response.json()["id"]
        
        # 3. 分配不同类型的设备
        ips_response = client.get(f"/api/subnets/{subnet_id}/ips", headers=headers)
        available_ips = ips_response.json()["items"][:10]
        
        device_types = ["Web Server", "Database Server", "Load Balancer", "Firewall"]
        for i, ip in enumerate(available_ips):
            if ip["status"] == "available":
                allocation_data = {
                    "hostname": f"device-{i+1}",
                    "device_type": device_types[i % len(device_types)],
                    "assigned_to": f"Team {chr(65 + i % 3)}",  # Team A, B, C
                    "mac_address": f"AA:BB:CC:DD:EE:{i:02d}"
                }
                client.post(f"/api/ips/{ip['ip_address']}/allocate", json=allocation_data, headers=headers)
        
        # 4. 按设备类型搜索
        search_response = client.get("/api/ips/search?device_type=Web Server", headers=headers)
        assert search_response.status_code == 200
        web_servers = search_response.json()["items"]
        assert all("Web Server" in item["device_type"] for item in web_servers)
        
        # 5. 按主机名模式搜索
        hostname_search = client.get("/api/ips/search?hostname=device-1", headers=headers)
        assert hostname_search.status_code == 200
        hostname_results = hostname_search.json()["items"]
        assert len(hostname_results) >= 1
        
        # 6. 按状态过滤
        allocated_search = client.get("/api/ips/search?status=allocated", headers=headers)
        assert allocated_search.status_code == 200
        allocated_results = allocated_search.json()["items"]
        assert all(item["status"] == "allocated" for item in allocated_results)
        
        # 7. 组合搜索条件
        complex_search = client.get(
            "/api/ips/search?device_type=Database&assigned_to=Team A",
            headers=headers
        )
        assert complex_search.status_code == 200
        
        # 8. 搜索网段
        subnet_search = client.get("/api/subnets/search?description=Search Test", headers=headers)
        assert subnet_search.status_code == 200
        subnet_results = subnet_search.json()["items"]
        assert len(subnet_results) >= 1

    @pytest.mark.e2e
    def test_error_recovery_workflow(self, client, db_session):
        """测试错误恢复工作流程"""
        # 1. 创建用户并登录
        user = UserFactory(username="error_test_user", role="admin")
        db_session.add(user)
        db_session.commit()
        
        login_response = client.post("/api/auth/login", json={
            "username": "error_test_user",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 尝试创建无效网段
        invalid_subnet = {
            "network": "invalid_network",
            "netmask": "255.255.255.0"
        }
        error_response = client.post("/api/subnets", json=invalid_subnet, headers=headers)
        assert error_response.status_code == 422
        
        # 3. 创建有效网段
        valid_subnet = {
            "network": "10.20.0.0/24",
            "netmask": "255.255.255.0",
            "gateway": "10.20.0.1",
            "description": "Error Recovery Test"
        }
        success_response = client.post("/api/subnets", json=valid_subnet, headers=headers)
        assert success_response.status_code == 201
        subnet_id = success_response.json()["id"]
        
        # 4. 尝试分配不存在的IP
        nonexistent_ip_response = client.post(
            "/api/ips/999.999.999.999/allocate",
            json={"hostname": "test"},
            headers=headers
        )
        assert nonexistent_ip_response.status_code == 404
        
        # 5. 分配有效IP
        ips_response = client.get(f"/api/subnets/{subnet_id}/ips", headers=headers)
        available_ip = next(ip for ip in ips_response.json()["items"] if ip["status"] == "available")
        
        valid_allocation = {
            "hostname": "recovery-test-server",
            "device_type": "Server"
        }
        allocation_response = client.post(
            f"/api/ips/{available_ip['ip_address']}/allocate",
            json=valid_allocation,
            headers=headers
        )
        assert allocation_response.status_code == 200
        
        # 6. 尝试重复分配同一IP
        duplicate_response = client.post(
            f"/api/ips/{available_ip['ip_address']}/allocate",
            json=valid_allocation,
            headers=headers
        )
        assert duplicate_response.status_code == 400
        
        # 7. 验证系统状态一致性
        final_check = client.get(f"/api/ips/{available_ip['ip_address']}", headers=headers)
        assert final_check.status_code == 200
        final_ip_state = final_check.json()
        assert final_ip_state["status"] == "allocated"
        assert final_ip_state["hostname"] == "recovery-test-server"