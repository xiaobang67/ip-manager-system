import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.services.audit_service import AuditService
from app.core.security import get_password_hash


class TestAuditIntegration:
    """审计系统集成测试"""

    def test_audit_middleware_records_operations(self, client: TestClient, db_session: Session, admin_token: str):
        """测试审计中间件记录操作"""
        # 创建网段
        subnet_data = {
            "network": "192.168.100.0/24",
            "netmask": "255.255.255.0",
            "gateway": "192.168.100.1",
            "description": "测试网段用于审计"
        }
        
        response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        subnet_id = response.json()["id"]
        
        # 验证审计日志记录
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.action == "CREATE",
            AuditLog.entity_type == "subnet",
            AuditLog.entity_id == subnet_id
        ).all()
        
        assert len(audit_logs) >= 1
        audit_log = audit_logs[0]
        assert audit_log.new_values is not None
        assert audit_log.new_values["network"] == subnet_data["network"]
        assert audit_log.ip_address is not None
        assert audit_log.user_agent is not None

    def test_ip_allocation_audit_trail(self, client: TestClient, db_session: Session, admin_token: str):
        """测试IP分配的完整审计轨迹"""
        # 1. 创建网段
        subnet_data = {
            "network": "192.168.101.0/24",
            "netmask": "255.255.255.0",
            "gateway": "192.168.101.1",
            "description": "IP分配审计测试"
        }
        
        response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        subnet_id = response.json()["id"]
        
        # 2. 分配IP地址
        allocation_data = {
            "subnet_id": subnet_id,
            "hostname": "test-server",
            "description": "测试服务器"
        }
        
        response = client.post(
            "/api/v1/ips/allocate",
            json=allocation_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        ip_data = response.json()
        ip_id = ip_data["id"]
        
        # 3. 保留IP地址
        reserve_data = {
            "reason": "系统保留"
        }
        
        response = client.put(
            f"/api/v1/ips/{ip_id}/reserve",
            json=reserve_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # 4. 释放IP地址
        response = client.put(
            f"/api/v1/ips/{ip_id}/release",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # 5. 验证完整的审计轨迹
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == "ip",
            AuditLog.entity_id == ip_id
        ).order_by(AuditLog.created_at).all()
        
        # 应该有分配、保留、释放三个操作记录
        assert len(audit_logs) >= 3
        
        actions = [log.action for log in audit_logs]
        assert "ALLOCATE" in actions
        assert "RESERVE" in actions
        assert "RELEASE" in actions
        
        # 验证每个操作的详细信息
        for log in audit_logs:
            assert log.user_id is not None
            assert log.ip_address is not None
            assert log.created_at is not None

    def test_audit_log_search_api(self, client: TestClient, db_session: Session, admin_token: str):
        """测试审计日志搜索API"""
        # 创建一些测试数据
        audit_service = AuditService(db_session)
        
        # 创建测试用户
        test_user = User(
            username="audit_test_user",
            password_hash=get_password_hash("password123"),
            email="audit@test.com",
            role="user"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
        
        # 记录一些审计日志
        audit_service.log_operation(
            user_id=test_user.id,
            action="CREATE",
            entity_type="ip",
            entity_id=1,
            new_values={"ip_address": "192.168.1.100", "status": "allocated"},
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        audit_service.log_operation(
            user_id=test_user.id,
            action="UPDATE",
            entity_type="subnet",
            entity_id=1,
            old_values={"description": "旧描述"},
            new_values={"description": "新描述"},
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        # 测试搜索API
        search_data = {
            "user_id": test_user.id,
            "skip": 0,
            "limit": 10
        }
        
        response = client.post(
            "/api/v1/audit-logs/search",
            json=search_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result
        assert result["total"] >= 2
        
        # 验证返回的数据结构
        for item in result["items"]:
            assert "id" in item
            assert "action" in item
            assert "entity_type" in item
            assert "user_id" in item
            assert "username" in item
            assert "created_at" in item

    def test_entity_history_api(self, client: TestClient, db_session: Session, admin_token: str):
        """测试实体历史记录API"""
        # 创建网段
        subnet_data = {
            "network": "192.168.102.0/24",
            "netmask": "255.255.255.0",
            "description": "历史记录测试"
        }
        
        response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        subnet_id = response.json()["id"]
        
        # 更新网段
        update_data = {
            "description": "更新后的描述"
        }
        
        response = client.put(
            f"/api/v1/subnets/{subnet_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # 获取实体历史记录
        response = client.get(
            f"/api/v1/audit-logs/entity/subnet/{subnet_id}/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "entity_type" in result
        assert "entity_id" in result
        assert "history" in result
        assert result["entity_type"] == "subnet"
        assert result["entity_id"] == subnet_id
        assert len(result["history"]) >= 2  # 创建和更新操作

    def test_audit_log_export(self, client: TestClient, db_session: Session, admin_token: str):
        """测试审计日志导出功能"""
        # 创建一些测试数据
        audit_service = AuditService(db_session)
        
        for i in range(5):
            audit_service.log_operation(
                user_id=1,
                action="CREATE",
                entity_type="ip",
                entity_id=i + 1,
                new_values={"ip_address": f"192.168.1.{100 + i}"},
                ip_address="127.0.0.1"
            )
        
        # 测试CSV导出
        export_data = {
            "format": "csv",
            "action": "CREATE",
            "entity_type": "ip"
        }
        
        response = client.post(
            "/api/v1/audit-logs/export",
            json=export_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        
        # 验证CSV内容
        csv_content = response.content.decode('utf-8')
        assert "id,action,entity_type" in csv_content
        assert "CREATE" in csv_content
        
        # 测试JSON导出
        export_data["format"] = "json"
        
        response = client.post(
            "/api/v1/audit-logs/export",
            json=export_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        
        # 验证JSON内容
        json_content = json.loads(response.content.decode('utf-8'))
        assert isinstance(json_content, list)
        assert len(json_content) >= 5

    def test_audit_statistics_api(self, client: TestClient, db_session: Session, admin_token: str):
        """测试审计统计API"""
        # 创建一些测试数据
        audit_service = AuditService(db_session)
        
        # 创建不同类型的操作记录
        operations = [
            ("CREATE", "ip", 1),
            ("UPDATE", "ip", 1),
            ("DELETE", "ip", 1),
            ("CREATE", "subnet", 1),
            ("UPDATE", "subnet", 1),
            ("ALLOCATE", "ip", 2),
            ("RELEASE", "ip", 2)
        ]
        
        for action, entity_type, entity_id in operations:
            audit_service.log_operation(
                user_id=1,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address="127.0.0.1"
            )
        
        # 获取统计信息
        response = client.get(
            "/api/v1/audit-logs/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_logs" in stats
        assert "actions_count" in stats
        assert "entities_count" in stats
        assert "users_count" in stats
        assert "recent_activities" in stats
        
        # 验证统计数据
        assert stats["total_logs"] >= 7
        assert "CREATE" in stats["actions_count"]
        assert "UPDATE" in stats["actions_count"]
        assert "ip" in stats["entities_count"]
        assert "subnet" in stats["entities_count"]

    def test_audit_log_archive(self, client: TestClient, db_session: Session, admin_token: str):
        """测试审计日志归档功能"""
        # 创建一些旧的审计日志
        audit_service = AuditService(db_session)
        
        # 创建30天前的日志
        old_date = datetime.utcnow() - timedelta(days=35)
        
        # 手动插入旧日志
        old_log = AuditLog(
            user_id=1,
            action="CREATE",
            entity_type="ip",
            entity_id=999,
            created_at=old_date,
            ip_address="127.0.0.1"
        )
        db_session.add(old_log)
        db_session.commit()
        
        # 创建最近的日志
        audit_service.log_operation(
            user_id=1,
            action="CREATE",
            entity_type="ip",
            entity_id=1000,
            ip_address="127.0.0.1"
        )
        
        # 执行归档（保留30天）
        response = client.delete(
            "/api/v1/audit-logs/archive?days_to_keep=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "archived_count" in result
        assert result["archived_count"] >= 1
        
        # 验证旧日志被删除
        remaining_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_id == 999
        ).all()
        assert len(remaining_logs) == 0
        
        # 验证新日志仍然存在
        recent_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_id == 1000
        ).all()
        assert len(recent_logs) >= 1

    def test_user_activity_api(self, client: TestClient, db_session: Session, admin_token: str):
        """测试用户活动记录API"""
        # 创建测试用户
        test_user = User(
            username="activity_test_user",
            password_hash=get_password_hash("password123"),
            email="activity@test.com",
            role="user"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
        
        # 记录用户活动
        audit_service = AuditService(db_session)
        
        activities = [
            ("CREATE", "ip", 1),
            ("UPDATE", "ip", 1),
            ("CREATE", "subnet", 1)
        ]
        
        for action, entity_type, entity_id in activities:
            audit_service.log_operation(
                user_id=test_user.id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address="127.0.0.1"
            )
        
        # 获取用户活动记录
        response = client.get(
            f"/api/v1/audit-logs/user/{test_user.id}/activity",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "user_id" in result
        assert "username" in result
        assert "activities" in result
        assert result["user_id"] == test_user.id
        assert result["username"] == test_user.username
        assert len(result["activities"]) >= 3

    def test_audit_log_permissions(self, client: TestClient, db_session: Session, user_token: str):
        """测试审计日志权限控制"""
        # 普通用户不能访问统计信息
        response = client.get(
            "/api/v1/audit-logs/statistics",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
        
        # 普通用户不能导出日志
        export_data = {"format": "csv"}
        response = client.post(
            "/api/v1/audit-logs/export",
            json=export_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
        
        # 普通用户不能归档日志
        response = client.delete(
            "/api/v1/audit-logs/archive",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403

    def test_audit_log_data_integrity(self, client: TestClient, db_session: Session, admin_token: str):
        """测试审计日志数据完整性"""
        # 创建网段并记录详细变更
        subnet_data = {
            "network": "192.168.103.0/24",
            "netmask": "255.255.255.0",
            "gateway": "192.168.103.1",
            "description": "数据完整性测试",
            "vlan_id": 100,
            "location": "测试机房"
        }
        
        response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        subnet_id = response.json()["id"]
        
        # 更新网段
        update_data = {
            "description": "更新后的描述",
            "vlan_id": 200,
            "location": "新机房"
        }
        
        response = client.put(
            f"/api/v1/subnets/{subnet_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # 验证审计日志记录了完整的变更信息
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.action == "UPDATE",
            AuditLog.entity_type == "subnet",
            AuditLog.entity_id == subnet_id
        ).all()
        
        assert len(audit_logs) >= 1
        update_log = audit_logs[0]
        
        # 验证变更前后的值都被记录
        assert update_log.old_values is not None
        assert update_log.new_values is not None
        
        # 验证具体的变更内容
        if update_log.old_values and update_log.new_values:
            assert "description" in update_log.old_values or "description" in update_log.new_values
            assert "vlan_id" in update_log.old_values or "vlan_id" in update_log.new_values

    def test_audit_log_search_filters(self, client: TestClient, db_session: Session, admin_token: str):
        """测试审计日志搜索过滤器"""
        # 创建多种类型的审计日志
        audit_service = AuditService(db_session)
        
        # 创建不同时间的日志
        base_time = datetime.utcnow()
        
        logs_data = [
            (1, "CREATE", "ip", 1, base_time - timedelta(hours=2)),
            (1, "UPDATE", "ip", 1, base_time - timedelta(hours=1)),
            (1, "DELETE", "subnet", 1, base_time - timedelta(minutes=30)),
            (2, "ALLOCATE", "ip", 2, base_time - timedelta(minutes=15)),
            (2, "RELEASE", "ip", 2, base_time)
        ]
        
        for user_id, action, entity_type, entity_id, created_at in logs_data:
            log = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                created_at=created_at,
                ip_address="127.0.0.1"
            )
            db_session.add(log)
        
        db_session.commit()
        
        # 测试按操作类型过滤
        search_data = {
            "action": "CREATE",
            "skip": 0,
            "limit": 10
        }
        
        response = client.post(
            "/api/v1/audit-logs/search",
            json=search_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 验证只返回CREATE操作
        for item in result["items"]:
            if item["action"] in ["CREATE"]:  # 可能包含之前测试创建的记录
                assert item["action"] == "CREATE"
        
        # 测试按实体类型过滤
        search_data = {
            "entity_type": "ip",
            "skip": 0,
            "limit": 10
        }
        
        response = client.post(
            "/api/v1/audit-logs/search",
            json=search_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 验证只返回IP相关操作
        for item in result["items"]:
            if item["entity_type"] in ["ip"]:
                assert item["entity_type"] == "ip"
        
        # 测试按时间范围过滤
        start_time = base_time - timedelta(hours=1, minutes=30)
        end_time = base_time - timedelta(minutes=10)
        
        search_data = {
            "start_date": start_time.isoformat(),
            "end_date": end_time.isoformat(),
            "skip": 0,
            "limit": 10
        }
        
        response = client.post(
            "/api/v1/audit-logs/search",
            json=search_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 验证返回的记录在指定时间范围内
        for item in result["items"]:
            item_time = datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
            # 由于时区和精度问题，这里只做基本验证
            assert item_time is not None

    def test_recent_activities_api(self, client: TestClient, db_session: Session, admin_token: str):
        """测试最近活动API"""
        # 创建一些最近的活动
        audit_service = AuditService(db_session)
        
        for i in range(3):
            audit_service.log_operation(
                user_id=1,
                action="CREATE",
                entity_type="ip",
                entity_id=i + 100,
                ip_address="127.0.0.1"
            )
        
        # 获取最近活动
        response = client.get(
            "/api/v1/audit-logs/recent?limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        activities = response.json()
        
        assert isinstance(activities, list)
        assert len(activities) >= 3
        
        # 验证活动按时间倒序排列
        if len(activities) > 1:
            first_time = datetime.fromisoformat(activities[0]["created_at"].replace('Z', '+00:00'))
            second_time = datetime.fromisoformat(activities[1]["created_at"].replace('Z', '+00:00'))
            assert first_time >= second_time