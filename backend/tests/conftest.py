"""
测试配置和fixtures
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import User, Subnet, IPAddress
from app.auth import create_access_token
from app.core.security import get_password_hash
import os
from typing import AsyncGenerator


# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# 创建测试会话
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """覆盖数据库依赖"""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# 覆盖应用的数据库依赖
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """设置测试数据库"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理数据库
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """数据库会话fixture"""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """HTTP客户端fixture"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        role="user",
        theme="light",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """创建测试管理员"""
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        role="admin",
        theme="light",
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_manager(db_session: AsyncSession) -> User:
    """创建测试网络管理员"""
    manager = User(
        username="manager",
        email="manager@example.com",
        password_hash=get_password_hash("managerpass123"),
        role="manager",
        theme="light",
        is_active=True
    )
    db_session.add(manager)
    await db_session.commit()
    await db_session.refresh(manager)
    return manager


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """认证头fixture"""
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(test_admin: User) -> dict:
    """管理员认证头fixture"""
    token = create_access_token(data={"sub": test_admin.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers(test_manager: User) -> dict:
    """管理员认证头fixture"""
    token = create_access_token(data={"sub": test_manager.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(test_user: User) -> dict:
    """普通用户认证头fixture"""
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_subnet(db_session: AsyncSession, test_user: User) -> Subnet:
    """创建测试网段"""
    subnet = Subnet(
        network="192.168.1.0/24",
        netmask="255.255.255.0",
        gateway="192.168.1.1",
        description="Test Network",
        vlan_id=100,
        location="Test Location",
        created_by=test_user.id
    )
    db_session.add(subnet)
    await db_session.commit()
    await db_session.refresh(subnet)
    return subnet


@pytest.fixture
async def test_subnet_with_ips(db_session: AsyncSession, test_user: User) -> Subnet:
    """创建带IP地址的测试网段"""
    subnet = Subnet(
        network="192.168.2.0/24",
        netmask="255.255.255.0",
        gateway="192.168.2.1",
        description="Test Network with IPs",
        vlan_id=200,
        location="Test Location",
        created_by=test_user.id
    )
    db_session.add(subnet)
    await db_session.flush()
    
    # 创建一些IP地址
    for i in range(1, 11):  # 创建10个IP地址
        ip = IPAddress(
            ip_address=f"192.168.2.{i}",
            subnet_id=subnet.id,
            status="available"
        )
        db_session.add(ip)
    
    await db_session.commit()
    await db_session.refresh(subnet)
    return subnet


@pytest.fixture
async def test_allocated_ip(db_session: AsyncSession, test_subnet_with_ips: Subnet, test_user: User) -> IPAddress:
    """创建已分配的测试IP地址"""
    ip = IPAddress(
        ip_address="192.168.2.100",
        subnet_id=test_subnet_with_ips.id,
        status="allocated",
        mac_address="00:11:22:33:44:55",
        hostname="test-server",
        device_type="Server",
        assigned_to="IT Department",
        description="Test allocated IP",
        allocated_by=test_user.id
    )
    db_session.add(ip)
    await db_session.commit()
    await db_session.refresh(ip)
    return ip


@pytest.fixture
async def test_reserved_ip(db_session: AsyncSession, test_subnet_with_ips: Subnet) -> IPAddress:
    """创建保留的测试IP地址"""
    ip = IPAddress(
        ip_address="192.168.2.200",
        subnet_id=test_subnet_with_ips.id,
        status="reserved",
        description="Reserved for future use"
    )
    db_session.add(ip)
    await db_session.commit()
    await db_session.refresh(ip)
    return ip


@pytest.fixture
def sample_subnet_data() -> dict:
    """示例网段数据"""
    return {
        "network": "10.0.0.0/16",
        "netmask": "255.255.0.0",
        "gateway": "10.0.0.1",
        "description": "Sample Network",
        "vlan_id": 300,
        "location": "Sample Location"
    }


@pytest.fixture
def sample_user_data() -> dict:
    """示例用户数据"""
    return {
        "username": "sampleuser",
        "email": "sample@example.com",
        "password": "samplepass123",
        "role": "user",
        "theme": "light"
    }


@pytest.fixture
def sample_ip_allocation_data() -> dict:
    """示例IP分配数据"""
    return {
        "mac_address": "00:AA:BB:CC:DD:EE",
        "hostname": "sample-host",
        "device_type": "Workstation",
        "assigned_to": "Sample Department",
        "description": "Sample IP allocation"
    }


# 测试数据清理fixture
@pytest.fixture(autouse=True)
async def cleanup_test_data(db_session: AsyncSession):
    """自动清理测试数据"""
    yield
    
    # 测试后清理数据
    try:
        # 删除所有测试数据
        await db_session.execute("DELETE FROM audit_logs")
        await db_session.execute("DELETE FROM ip_addresses")
        await db_session.execute("DELETE FROM subnets")
        await db_session.execute("DELETE FROM users WHERE username LIKE 'test%' OR username LIKE 'sample%'")
        await db_session.commit()
    except Exception:
        await db_session.rollback()


# 性能测试fixtures
@pytest.fixture
def performance_test_data():
    """性能测试数据"""
    return {
        "large_subnet_count": 100,
        "large_ip_count": 1000,
        "concurrent_requests": 50
    }


# Mock fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis客户端"""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ex=None):
            self.data[key] = value
        
        async def delete(self, key):
            self.data.pop(key, None)
        
        async def exists(self, key):
            return key in self.data
    
    return MockRedis()


@pytest.fixture
def mock_email_service():
    """Mock邮件服务"""
    class MockEmailService:
        def __init__(self):
            self.sent_emails = []
        
        async def send_email(self, to, subject, body):
            self.sent_emails.append({
                "to": to,
                "subject": subject,
                "body": body
            })
            return True
    
    return MockEmailService()


# 测试环境配置
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """设置测试环境"""
    # 设置测试环境变量
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    
    yield
    
    # 清理环境变量
    os.environ.pop("TESTING", None)


# 并发测试fixtures
@pytest.fixture
async def concurrent_clients(setup_database):
    """并发客户端fixture"""
    clients = []
    for i in range(5):
        client = AsyncClient(app=app, base_url="http://test")
        clients.append(client)
    
    yield clients
    
    # 关闭所有客户端
    for client in clients:
        await client.aclose()


# 数据库事务测试fixture
@pytest.fixture
async def transaction_test_session(setup_database):
    """事务测试会话"""
    async with TestSessionLocal() as session:
        async with session.begin():
            yield session
            # 事务会自动回滚


# 测试数据生成器
class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def generate_subnet_data(network_base="192.168", count=1):
        """生成网段测试数据"""
        subnets = []
        for i in range(count):
            subnets.append({
                "network": f"{network_base}.{i}.0/24",
                "netmask": "255.255.255.0",
                "gateway": f"{network_base}.{i}.1",
                "description": f"Test Network {i}",
                "vlan_id": 100 + i,
                "location": f"Test Location {i}"
            })
        return subnets
    
    @staticmethod
    def generate_user_data(count=1):
        """生成用户测试数据"""
        users = []
        for i in range(count):
            users.append({
                "username": f"testuser{i}",
                "email": f"testuser{i}@example.com",
                "password": f"testpass{i}123",
                "role": "user",
                "theme": "light"
            })
        return users
    
    @staticmethod
    def generate_ip_data(subnet_base="192.168.1", count=10):
        """生成IP地址测试数据"""
        ips = []
        for i in range(1, count + 1):
            ips.append({
                "ip_address": f"{subnet_base}.{i}",
                "status": "available"
            })
        return ips


@pytest.fixture
def test_data_generator():
    """测试数据生成器fixture"""
    return TestDataGenerator()