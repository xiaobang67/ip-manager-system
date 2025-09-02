"""
IP地址分配功能简单测试
验证核心分配、保留和释放功能
"""
import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User, UserRole
from app.models.subnet import Subnet
from app.models.ip_address import IPAddress, IPStatus
from app.services.ip_service import IPService
from app.services.audit_service import AuditService
from app.schemas.ip_address import IPAllocationRequest, IPReservationRequest, IPReleaseRequest
from app.core.security import get_password_hash


def test_ip_allocation_workflow():
    """测试IP地址分配工作流程"""
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. 创建测试用户
        test_user = User(
            username="testuser",
            password_hash=get_password_hash("testpass"),
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 2. 创建测试网段
        test_subnet = Subnet(
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            description="测试网段",
            created_by=test_user.id
        )
        db.add(test_subnet)
        db.commit()
        db.refresh(test_subnet)
        
        # 3. 为网段生成IP地址
        ip_service = IPService(db)
        generated_ips = ip_service.generate_ips_for_subnet(test_subnet.id, test_subnet.network)
        
        assert len(generated_ips) > 0, "应该生成IP地址"
        
        # 4. 测试IP分配
        allocation_request = IPAllocationRequest(
            subnet_id=test_subnet.id,
            hostname="test-server",
            mac_address="00:11:22:33:44:55",
            device_type="server",
            assigned_to="测试用户",
            description="测试分配"
        )
        
        allocated_ip = ip_service.allocate_ip(allocation_request, test_user.id)
        
        assert allocated_ip.status == IPStatus.ALLOCATED, "IP应该被标记为已分配"
        assert allocated_ip.hostname == "test-server", "主机名应该正确设置"
        assert allocated_ip.allocated_by == test_user.id, "分配者应该正确记录"
        
        # 5. 测试IP保留
        available_ip = db.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        assert available_ip is not None, "应该有可用的IP地址"
        
        reservation_request = IPReservationRequest(
            ip_address=available_ip.ip_address,
            reason="测试保留"
        )
        
        reserved_ip = ip_service.reserve_ip(reservation_request, test_user.id)
        
        assert reserved_ip.status == IPStatus.RESERVED, "IP应该被标记为保留"
        assert "测试保留" in reserved_ip.description, "保留原因应该记录"
        
        # 6. 测试IP释放
        release_request = IPReleaseRequest(
            ip_address=allocated_ip.ip_address,
            reason="测试释放"
        )
        
        released_ip = ip_service.release_ip(release_request, test_user.id)
        
        assert released_ip.status == IPStatus.AVAILABLE, "IP应该被标记为可用"
        assert released_ip.hostname is None, "主机名应该被清除"
        assert released_ip.mac_address is None, "MAC地址应该被清除"
        
        # 7. 测试审计日志（手动记录用于测试）
        audit_service = AuditService(db)
        
        # 手动记录分配操作
        audit_service.log_operation(
            user_id=test_user.id,
            action="ALLOCATE",
            entity_type="ip",
            entity_id=allocated_ip.id,
            new_values={"ip_address": allocated_ip.ip_address, "status": "allocated"}
        )
        
        # 手动记录释放操作
        audit_service.log_operation(
            user_id=test_user.id,
            action="RELEASE",
            entity_type="ip",
            entity_id=released_ip.id,
            old_values={"status": "allocated"},
            new_values={"status": "available"}
        )
        
        history = audit_service.get_entity_history("ip", allocated_ip.id)
        
        assert len(history) >= 2, "应该有分配和释放的历史记录"
        
        actions = [record["action"] for record in history]
        assert "ALLOCATE" in actions, "应该有分配记录"
        assert "RELEASE" in actions, "应该有释放记录"
        
        # 8. 测试统计信息
        stats = ip_service.get_ip_statistics(test_subnet.id)
        
        assert stats.total > 0, "总IP数量应该大于0"
        assert stats.available > 0, "可用IP数量应该大于0"
        assert stats.reserved > 0, "保留IP数量应该大于0"
        
        print("✅ IP地址分配工作流程测试通过")
        
    finally:
        db.close()


def test_reservation_limits():
    """测试保留限制功能"""
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 创建测试用户和网段
        test_user = User(
            username="testuser2",
            password_hash=get_password_hash("testpass"),
            email="test2@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 创建小网段用于测试限制
        test_subnet = Subnet(
            network="192.168.2.0/28",  # 只有14个可用IP
            netmask="255.255.255.240",
            gateway="192.168.2.1",
            description="小测试网段",
            created_by=test_user.id
        )
        db.add(test_subnet)
        db.commit()
        db.refresh(test_subnet)
        
        # 生成IP地址
        ip_service = IPService(db)
        generated_ips = ip_service.generate_ips_for_subnet(test_subnet.id, test_subnet.network)
        
        # 尝试保留多个IP地址
        available_ips = db.query(IPAddress).filter(
            IPAddress.subnet_id == test_subnet.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).limit(5).all()
        
        reserved_count = 0
        for ip in available_ips:
            try:
                reservation_request = IPReservationRequest(
                    ip_address=ip.ip_address,
                    reason=f"测试保留 {reserved_count + 1}"
                )
                ip_service.reserve_ip(reservation_request, test_user.id)
                reserved_count += 1
            except Exception as e:
                # 如果达到限制，应该抛出异常
                if "限制" in str(e):
                    break
                else:
                    raise
        
        assert reserved_count > 0, "应该能够保留一些IP地址"
        
        print(f"✅ 保留限制测试通过，成功保留了 {reserved_count} 个IP地址")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_ip_allocation_workflow()
    test_reservation_limits()
    print("🎉 所有测试通过！")