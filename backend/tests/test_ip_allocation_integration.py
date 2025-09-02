"""
IP地址分配功能集成测试
测试IP地址分配、保留和释放的完整流程
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.subnet import Subnet
from app.models.ip_address import IPAddress, IPStatus
from app.models.audit_log import AuditLog
from app.services.ip_service import IPService


class TestIPAllocationIntegration:
    """IP地址分配集成测试类"""

    @pytest.fixture
    def test_subnet(self, db_session: Session, test_admin):
        """创建测试网段"""
        subnet = Subnet(
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            description="测试网段",
            created_by=test_admin.id
        )
        db_session.add(subnet)
        db_session.commit()
        db_session.refresh(subnet)
        
        # 为网段生成IP地址
        ip_service = IPService(db_session)
        ip_service.generate_ips_for_subnet(subnet.id, subnet.network)
        
        return subnet

    def test_allocate_ip_success(self, client: TestClient, db_session: Session, 
                                test_subnet, admin_headers):
        """测试成功分配IP地址"""
        allocation_data = {
            "subnet_id": test_subnet.id,
            "mac_address": "00:11:22:33:44:55",
            "hostname": "test-server",
            "device_type": "server",
            "location": "机房A",
            "assigned_to": "张三",
            "description": "测试服务器"
        }
        
        response = client.post(
            "/api/ips/allocate",
            json=allocation_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回数据
        assert data["subnet_id"] == test_subnet.id
        assert data["status"] == IPStatus.ALLOCATED
        assert data["mac_address"] == "00:11:22:33:44:55"
        assert data["hostname"] == "test-server"
        assert data["assigned_to"] == "张三"
        assert data["allocated_at"] is not None
        assert data["allocated_by"] is not None
        
        # 验证数据库中的记录
        ip_record = db_session.query(IPAddress).filter(
            IPAddress.ip_address == data["ip_address"]
        ).first()
        assert ip_record is not None
        assert ip_record.status == IPStatus.ALLOCATED
        assert ip_record.mac_address == "00:11:22:33:44:55"
        
        # 验证审计日志
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.action == "ALLOCATE",
            AuditLog.entity_type == "ip",
            AuditLog.entity_id == ip_record.id
        ).first()
        assert audit_log is not None
        assert audit_log.new_values["ip_address"] == data["ip_address"]

    def test_allocate_preferred_ip_success(self, client: TestClient, db_session: Session,
                                         test_subnet, admin_headers):
        """测试分配指定的首选IP地址"""
        # 获取一个可用的IP地址
        available_ip = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        allocation_data = {
            "subnet_id": test_subnet.id,
            "preferred_ip": available_ip.ip_address,
            "hostname": "preferred-server",
            "assigned_to": "李四"
        }
        
        response = client.post(
            "/api/ips/allocate",
            json=allocation_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ip_address"] == available_ip.ip_address
        assert data["status"] == IPStatus.ALLOCATED
        assert data["hostname"] == "preferred-server"

    def test_allocate_ip_conflict(self, client: TestClient, db_session: Session,
                                 test_subnet, admin_headers):
        """测试分配已被占用的IP地址时的冲突处理"""
        # 先分配一个IP
        available_ip = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        # 手动设置为已分配状态
        available_ip.status = IPStatus.ALLOCATED
        db_session.commit()
        
        allocation_data = {
            "subnet_id": test_subnet.id,
            "preferred_ip": available_ip.ip_address,
            "hostname": "conflict-server"
        }
        
        response = client.post(
            "/api/ips/allocate",
            json=allocation_data,
            headers=admin_headers
        )
        
        assert response.status_code == 409
        assert "不可用" in response.json()["detail"]

    def test_reserve_ip_success(self, client: TestClient, db_session: Session,
                               test_subnet, admin_headers):
        """测试成功保留IP地址"""
        # 获取一个可用的IP地址
        available_ip = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        reservation_data = {
            "ip_address": available_ip.ip_address,
            "reason": "为新项目保留"
        }
        
        response = client.post(
            "/api/ips/reserve",
            json=reservation_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回数据
        assert data["ip_address"] == available_ip.ip_address
        assert data["status"] == IPStatus.RESERVED
        assert "保留 - 为新项目保留" in data["assigned_to"]
        assert data["allocated_at"] is not None
        
        # 验证数据库记录
        db_session.refresh(available_ip)
        assert available_ip.status == IPStatus.RESERVED
        
        # 验证审计日志
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.action == "RESERVE",
            AuditLog.entity_type == "ip",
            AuditLog.entity_id == available_ip.id
        ).first()
        assert audit_log is not None

    def test_reserve_ip_not_available(self, client: TestClient, db_session: Session,
                                    test_subnet, admin_headers):
        """测试保留不可用IP地址的错误处理"""
        # 获取一个IP并设置为已分配状态
        ip_record = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        ip_record.status = IPStatus.ALLOCATED
        db_session.commit()
        
        reservation_data = {
            "ip_address": ip_record.ip_address,
            "reason": "尝试保留已分配的IP"
        }
        
        response = client.post(
            "/api/ips/reserve",
            json=reservation_data,
            headers=admin_headers
        )
        
        assert response.status_code == 409
        assert "不可用" in response.json()["detail"]

    def test_release_ip_success(self, client: TestClient, db_session: Session,
                               test_subnet, admin_headers):
        """测试成功释放IP地址"""
        # 先分配一个IP地址
        available_ip = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        # 设置为已分配状态
        available_ip.status = IPStatus.ALLOCATED
        available_ip.hostname = "to-be-released"
        available_ip.mac_address = "AA:BB:CC:DD:EE:FF"
        db_session.commit()
        
        release_data = {
            "ip_address": available_ip.ip_address,
            "reason": "设备下线"
        }
        
        response = client.post(
            "/api/ips/release",
            json=release_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回数据
        assert data["ip_address"] == available_ip.ip_address
        assert data["status"] == IPStatus.AVAILABLE
        assert data["mac_address"] is None
        assert data["hostname"] is None
        assert data["assigned_to"] is None
        
        # 验证数据库记录
        db_session.refresh(available_ip)
        assert available_ip.status == IPStatus.AVAILABLE
        assert available_ip.mac_address is None
        assert available_ip.hostname is None
        
        # 验证审计日志
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.action == "RELEASE",
            AuditLog.entity_type == "ip",
            AuditLog.entity_id == available_ip.id
        ).first()
        assert audit_log is not None
        assert audit_log.old_values["hostname"] == "to-be-released"

    def test_release_reserved_ip_success(self, client: TestClient, db_session: Session,
                                       test_subnet, admin_headers):
        """测试成功释放保留的IP地址"""
        # 获取一个IP并设置为保留状态
        ip_record = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        ip_record.status = IPStatus.RESERVED
        ip_record.assigned_to = "保留 - 测试用途"
        db_session.commit()
        
        release_data = {
            "ip_address": ip_record.ip_address,
            "reason": "保留期结束"
        }
        
        response = client.post(
            "/api/ips/release",
            json=release_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == IPStatus.AVAILABLE

    def test_release_ip_invalid_status(self, client: TestClient, db_session: Session,
                                     test_subnet, admin_headers):
        """测试释放不可释放状态IP地址的错误处理"""
        # 获取一个可用的IP（不能释放可用状态的IP）
        available_ip = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        release_data = {
            "ip_address": available_ip.ip_address,
            "reason": "尝试释放可用IP"
        }
        
        response = client.post(
            "/api/ips/release",
            json=release_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "无法释放" in response.json()["detail"]

    def test_reservation_limits(self, client: TestClient, db_session: Session,
                              test_subnet, admin_headers):
        """测试保留IP地址的数量限制"""
        # 获取网段中的可用IP地址
        available_ips = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).limit(10).all()
        
        # 保留多个IP地址
        reserved_count = 0
        for ip in available_ips[:5]:  # 保留5个IP
            reservation_data = {
                "ip_address": ip.ip_address,
                "reason": f"批量保留测试 {reserved_count + 1}"
            }
            
            response = client.post(
                "/api/ips/reserve",
                json=reservation_data,
                headers=admin_headers
            )
            
            if response.status_code == 200:
                reserved_count += 1
            else:
                break
        
        # 验证至少保留了一些IP
        assert reserved_count > 0
        
        # 验证数据库中的保留记录
        reserved_ips = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.RESERVED
        ).count()
        
        assert reserved_ips == reserved_count

    def test_get_ip_history(self, client: TestClient, db_session: Session,
                           test_subnet, admin_headers):
        """测试获取IP地址历史记录"""
        # 获取一个可用IP并进行一系列操作
        available_ip = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        # 1. 分配IP
        allocation_data = {
            "subnet_id": test_subnet.id,
            "preferred_ip": available_ip.ip_address,
            "hostname": "history-test"
        }
        
        response = client.post(
            "/api/ips/allocate",
            json=allocation_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 2. 释放IP
        release_data = {
            "ip_address": available_ip.ip_address,
            "reason": "测试释放"
        }
        
        response = client.post(
            "/api/ips/release",
            json=release_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 3. 获取历史记录
        response = client.get(
            f"/api/ips/{available_ip.ip_address}/history",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        history = response.json()
        
        # 验证历史记录
        assert len(history) >= 2  # 至少有分配和释放两条记录
        
        # 验证记录内容
        actions = [record["action"] for record in history]
        assert "ALLOCATE" in actions
        assert "RELEASE" in actions

    def test_bulk_ip_operations(self, client: TestClient, db_session: Session,
                               test_subnet, admin_headers):
        """测试批量IP地址操作"""
        # 获取多个可用IP地址
        available_ips = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).limit(3).all()
        
        ip_addresses = [ip.ip_address for ip in available_ips]
        
        # 批量保留操作
        bulk_data = {
            "ip_addresses": ip_addresses,
            "operation": "reserve",
            "reason": "批量保留测试"
        }
        
        response = client.post(
            "/api/ips/bulk-operation",
            json=bulk_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 验证批量操作结果
        assert result["success_count"] == len(ip_addresses)
        assert result["failed_count"] == 0
        assert len(result["success_ips"]) == len(ip_addresses)
        
        # 验证数据库状态
        for ip_addr in ip_addresses:
            ip_record = db_session.query(IPAddress).filter(
                IPAddress.ip_address == ip_addr
            ).first()
            assert ip_record.status == IPStatus.RESERVED
        
        # 批量释放操作
        bulk_data["operation"] = "release"
        bulk_data["reason"] = "批量释放测试"
        
        response = client.post(
            "/api/ips/bulk-operation",
            json=bulk_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == len(ip_addresses)
        
        # 验证释放后的状态
        for ip_addr in ip_addresses:
            ip_record = db_session.query(IPAddress).filter(
                IPAddress.ip_address == ip_addr
            ).first()
            assert ip_record.status == IPStatus.AVAILABLE

    def test_ip_statistics(self, client: TestClient, db_session: Session,
                          test_subnet, admin_headers):
        """测试IP地址统计信息"""
        # 分配一些IP地址
        available_ips = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).limit(5).all()
        
        # 分配2个，保留2个
        for i, ip in enumerate(available_ips[:4]):
            if i < 2:
                ip.status = IPStatus.ALLOCATED
            else:
                ip.status = IPStatus.RESERVED
        
        db_session.commit()
        
        # 获取统计信息
        response = client.get(
            f"/api/ips/statistics?subnet_id={test_subnet.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        # 验证统计数据
        assert stats["allocated"] == 2
        assert stats["reserved"] == 2
        assert stats["total"] > 0
        assert stats["utilization_rate"] > 0

    def test_search_ips(self, client: TestClient, db_session: Session,
                       test_subnet, admin_headers):
        """测试IP地址搜索功能"""
        # 设置一些测试数据
        test_ip = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        test_ip.hostname = "search-test-server"
        test_ip.status = IPStatus.ALLOCATED
        db_session.commit()
        
        # 按主机名搜索
        response = client.get(
            "/api/ips/search?query=search-test",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        results = response.json()
        
        # 验证搜索结果
        assert len(results) > 0
        found = any(ip["hostname"] == "search-test-server" for ip in results)
        assert found
        
        # 按状态过滤
        response = client.get(
            f"/api/ips/search?subnet_id={test_subnet.id}&status=allocated",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        results = response.json()
        
        # 验证所有结果都是已分配状态
        for ip in results:
            assert ip["status"] == IPStatus.ALLOCATED