"""
测试数据工厂
使用Factory Boy创建测试数据
"""
import factory
from factory import Faker, SubFactory
from faker import Faker as FakerInstance
import ipaddress
from datetime import datetime, timedelta

from app.models.user import User, UserRole, UserTheme
from app.models.subnet import Subnet
from app.models.ip_address import IPAddress, IPStatus
from app.models.custom_field import CustomField, CustomFieldValue, FieldType
from app.models.tag import Tag, IPTag, SubnetTag
from app.models.audit_log import AuditLog
from app.models.alert import AlertRule, AlertHistory, AlertType, AlertSeverity
from app.core.security import get_password_hash

fake = FakerInstance()


class UserFactory(factory.Factory):
    """用户工厂"""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password_hash = factory.LazyFunction(lambda: get_password_hash("testpass123"))
    role = UserRole.USER
    theme = UserTheme.LIGHT
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class AdminUserFactory(UserFactory):
    """管理员用户工厂"""
    username = factory.Sequence(lambda n: f"admin{n}")
    role = UserRole.ADMIN


class SubnetFactory(factory.Factory):
    """网段工厂"""
    class Meta:
        model = Subnet

    network = factory.LazyFunction(
        lambda: str(fake.ipv4_network(address_class="private"))
    )
    netmask = "255.255.255.0"
    gateway = factory.LazyAttribute(
        lambda obj: str(ipaddress.ip_network(obj.network, strict=False).network_address + 1)
    )
    description = factory.Faker('text', max_nb_chars=100)
    vlan_id = factory.Faker('random_int', min=1, max=4094)
    location = factory.Faker('city')
    created_by = SubFactory(UserFactory)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class IPAddressFactory(factory.Factory):
    """IP地址工厂"""
    class Meta:
        model = IPAddress

    ip_address = factory.LazyAttribute(
        lambda obj: str(list(ipaddress.ip_network(obj.subnet.network, strict=False).hosts())[0])
    )
    subnet = SubFactory(SubnetFactory)
    status = IPStatus.AVAILABLE
    mac_address = factory.Faker('mac_address')
    hostname = factory.Faker('domain_word')
    device_type = factory.Faker('random_element', elements=['Server', 'Workstation', 'Router', 'Switch'])
    location = factory.Faker('city')
    assigned_to = factory.Faker('name')
    description = factory.Faker('text', max_nb_chars=200)
    allocated_by = SubFactory(UserFactory)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class AllocatedIPFactory(IPAddressFactory):
    """已分配IP地址工厂"""
    status = IPStatus.ALLOCATED
    allocated_at = factory.LazyFunction(datetime.utcnow)


class ReservedIPFactory(IPAddressFactory):
    """保留IP地址工厂"""
    status = IPStatus.RESERVED


class TagFactory(factory.Factory):
    """标签工厂"""
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"tag{n}")
    color = factory.Faker('hex_color')
    description = factory.Faker('text', max_nb_chars=100)
    created_at = factory.LazyFunction(datetime.utcnow)


class CustomFieldFactory(factory.Factory):
    """自定义字段工厂"""
    class Meta:
        model = CustomField

    entity_type = 'ip'
    field_name = factory.Sequence(lambda n: f"custom_field_{n}")
    field_type = FieldType.TEXT
    field_options = None
    is_required = False
    created_at = factory.LazyFunction(datetime.utcnow)


class CustomFieldValueFactory(factory.Factory):
    """自定义字段值工厂"""
    class Meta:
        model = CustomFieldValue

    field = SubFactory(CustomFieldFactory)
    entity_id = 1
    entity_type = 'ip'
    field_value = factory.Faker('text', max_nb_chars=50)


class AuditLogFactory(factory.Factory):
    """审计日志工厂"""
    class Meta:
        model = AuditLog

    user = SubFactory(UserFactory)
    action = factory.Faker('random_element', elements=['CREATE', 'UPDATE', 'DELETE', 'ALLOCATE', 'RELEASE'])
    entity_type = factory.Faker('random_element', elements=['ip', 'subnet', 'user'])
    entity_id = factory.Faker('random_int', min=1, max=1000)
    old_values = {}
    new_values = {}
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    created_at = factory.LazyFunction(datetime.utcnow)


class AlertRuleFactory(factory.Factory):
    """警报规则工厂"""
    class Meta:
        model = AlertRule

    name = factory.Sequence(lambda n: f"Alert Rule {n}")
    rule_type = AlertType.UTILIZATION
    threshold_value = factory.Faker('random_int', min=70, max=95)
    subnet = SubFactory(SubnetFactory)
    is_active = True
    notification_emails = '["admin@example.com"]'
    created_by = SubFactory(UserFactory)
    created_at = factory.LazyFunction(datetime.utcnow)


class AlertHistoryFactory(factory.Factory):
    """警报历史工厂"""
    class Meta:
        model = AlertHistory

    rule = SubFactory(AlertRuleFactory)
    alert_message = factory.Faker('text', max_nb_chars=200)
    severity = AlertSeverity.MEDIUM
    is_resolved = False
    resolved_at = None
    resolved_by = None
    created_at = factory.LazyFunction(datetime.utcnow)


# 便捷函数
def create_test_subnet_with_ips(ip_count=10, allocated_count=3):
    """创建包含IP地址的测试网段"""
    subnet = SubnetFactory()
    network = ipaddress.ip_network(subnet.network, strict=False)
    
    ips = []
    for i, ip in enumerate(list(network.hosts())[:ip_count]):
        if i < allocated_count:
            ip_obj = AllocatedIPFactory(subnet=subnet, ip_address=str(ip))
        else:
            ip_obj = IPAddressFactory(subnet=subnet, ip_address=str(ip))
        ips.append(ip_obj)
    
    return subnet, ips


def create_test_user_with_permissions(role=UserRole.USER):
    """创建具有特定权限的测试用户"""
    if role == UserRole.ADMIN:
        return AdminUserFactory()
    else:
        return UserFactory(role=role)